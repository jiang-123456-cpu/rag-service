from typing import List, Dict, Any
import torch
import os
from dotenv import load_dotenv
from sentence_transformers import CrossEncoder
from utils.config_handler import chroma_conf

# Optional import for HF Inference API fallback
try:
    from huggingface_hub import InferenceApi
except Exception:
    InferenceApi = None

# 加载环境变量
load_dotenv()


def check_and_download_reranker_model() -> None:
    """检查并下载/确保重排序模型存在（在 FastAPI 启动时调用）。

    如果 LOCAL_MODEL_PATH 指向一个已有本地模型目录则不做任何操作；否则尝试从 Hugging Face 下载到该路径。
    把输出改为无 emoji 以避免 Windows 控制台编码错误。
    """
    LOCAL_MODEL_PATH = chroma_conf["RERANKER_MODEL_PATH"]
    HF_MODEL_NAME = "Qwen/Qwen3-Reranker-0.6B"

    try:
        # 如果本地存在（且非空），直接返回
        if os.path.exists(LOCAL_MODEL_PATH) and os.path.isdir(LOCAL_MODEL_PATH) and os.listdir(LOCAL_MODEL_PATH):
            print(f"Detected local reranker model at: {LOCAL_MODEL_PATH}")
            return

        print(f"Local reranker model not found at: {LOCAL_MODEL_PATH}")
        print(f"Attempting to download {HF_MODEL_NAME} into {LOCAL_MODEL_PATH}")
        use_cache_folder = True
        try:
            os.makedirs(LOCAL_MODEL_PATH, exist_ok=True)
        except Exception as mkdir_e:
            # permission denied or path not creatable, fall back to default HF cache
            print(f"Warning: cannot create directory {LOCAL_MODEL_PATH}: {mkdir_e}; will use default HF cache instead")
            use_cache_folder = False

        device = "cuda" if torch.cuda.is_available() else "cpu"
        # Use CrossEncoder to download/cache the model into cache_folder (if possible)
        try:
            if use_cache_folder:
                _ = CrossEncoder(HF_MODEL_NAME, max_length=512, device=device, cache_folder=LOCAL_MODEL_PATH)
                print(f"Model downloaded/cached into {LOCAL_MODEL_PATH} (device={device})")
            else:
                _ = CrossEncoder(HF_MODEL_NAME, max_length=512, device=device)
                print(f"Model loaded from HF into default cache (device={device})")
        except Exception as e:
            # As a more robust fallback, try huggingface_hub snapshot_download if available and cache folder usable
            try:
                if use_cache_folder:
                    from huggingface_hub import snapshot_download
                    snapshot_download(repo_id=HF_MODEL_NAME, local_dir=LOCAL_MODEL_PATH)
                    print(f"Model snapshot_download succeeded into {LOCAL_MODEL_PATH}")
                else:
                    from huggingface_hub import snapshot_download
                    # let snapshot_download use default cache
                    snapshot_download(repo_id=HF_MODEL_NAME)
                    print(f"Model snapshot_download succeeded into HF cache")
            except Exception as e2:
                print(f"Failed to download model via CrossEncoder ({e}) and snapshot_download ({e2})")
                raise

    except Exception as e:
        # avoid printing non-encodable characters
        print(f"Model check/download failed: {e}")
        raise RuntimeError(f"Failed to ensure reranker model: {e}")


class ReorderService:
    """文档重排序服务"""

    def __init__(self):
        # 从环境变量读取重排序模型路径
        self.LOCAL_MODEL_PATH = chroma_conf["RERANKER_MODEL_PATH"]
        # Hugging Face模型名称
        self.HF_MODEL_NAME = "Qwen/Qwen3-Reranker-0.6B"
        # HF token for Inference API fallback
        self.hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
        # 自动选择设备（优先使用GPU）
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # 模型实例（懒加载）
        self._model = None
        # backend: 'crossencoder' or 'inference_api'
        self.backend = None

    async def _get_model(self):
        """懒加载模型实例

        优先从本地模型目录加载；若不存在或加载失败，尝试从 HF 加载；若网络不可用且提供 HF_TOKEN，可回退到 InferenceApi。
        """
        if self._model is None and self.backend != 'inference_api':
            # Try local directory first
            if os.path.exists(self.LOCAL_MODEL_PATH) and os.path.isdir(self.LOCAL_MODEL_PATH) and os.listdir(self.LOCAL_MODEL_PATH):
                try:
                    print(f"Loading local reranker from: {self.LOCAL_MODEL_PATH}")
                    self._model = CrossEncoder(self.LOCAL_MODEL_PATH, max_length=512, device=self.device, local_files_only=True)
                    self.backend = 'crossencoder'
                except Exception as e:
                    print(f"Failed to load local CrossEncoder at {self.LOCAL_MODEL_PATH}: {e}")

            if self._model is None:
                # Try loading by HF model name and cache to LOCAL_MODEL_PATH (if possible)
                try:
                    print(f"Attempting to load '{self.HF_MODEL_NAME}' from Hugging Face and cache to {self.LOCAL_MODEL_PATH}")
                    try:
                        os.makedirs(self.LOCAL_MODEL_PATH, exist_ok=True)
                        use_cache_folder = True
                    except Exception as mkdir_e:
                        print(f"Warning: cannot create directory {self.LOCAL_MODEL_PATH}: {mkdir_e}; will use default HF cache instead")
                        use_cache_folder = False

                    if use_cache_folder:
                        self._model = CrossEncoder(self.HF_MODEL_NAME, max_length=512, device=self.device, cache_folder=self.LOCAL_MODEL_PATH)
                    else:
                        self._model = CrossEncoder(self.HF_MODEL_NAME, max_length=512, device=self.device)
                    self.backend = 'crossencoder'
                except Exception as e:
                    print(f"Failed to load HF CrossEncoder '{self.HF_MODEL_NAME}': {e}")
                    # Try InferenceApi fallback if token exists
                    if self.hf_token and InferenceApi is not None:
                        try:
                            print("Falling back to HuggingFace InferenceApi (requires internet)")
                            self.api = InferenceApi(repo_id=self.HF_MODEL_NAME, token=self.hf_token)
                            self.backend = 'inference_api'
                        except Exception as ie:
                            print(f"InferenceApi init failed: {ie}")
                    else:
                        print("No HF token or InferenceApi unavailable; cannot use Inference API fallback")

            # finalize
            if self.backend == 'crossencoder' and self._model is not None:
                self._model.eval()
                print(f"Reranker CrossEncoder ready (device={self.device})")
            elif self.backend == 'inference_api':
                print("Reranker will use HuggingFace Inference API for scoring")

        return self._model

    @property
    async def model(self):
        """获取模型实例（懒加载）"""
        return await self._get_model()

    async def reorder_documents(self, query: str, documents: List[str]) -> Dict[str, Any]:
        """
        对文档进行重排序
        :param query: 查询语句
        :param documents: 文档列表
        :return: 包含重排序结果的字典，格式为：
                 {"success": bool, "documents": List[Dict], "error": str}
        """
        try:
            if not documents:
                return {
                    "success": True,
                    "documents": [],
                    "error": ""
                }

            # 构造查询+文档对
            pairs = [(query, doc) for doc in documents]

            # Decide whether to use heavyweight model or lightweight fallback
            scored_documents = []
            heavy_available = False
            try:
                if os.path.exists(self.LOCAL_MODEL_PATH) and os.path.isdir(self.LOCAL_MODEL_PATH) and os.listdir(self.LOCAL_MODEL_PATH):
                    heavy_available = True
                    self.backend = 'crossencoder'
                elif self.hf_token and InferenceApi is not None:
                    try:
                        self.api = InferenceApi(repo_id=self.HF_MODEL_NAME, token=self.hf_token)
                        self.backend = 'inference_api'
                        heavy_available = True
                    except Exception:
                        heavy_available = False
            except Exception:
                heavy_available = False

            model = None
            if heavy_available:
                try:
                    model = await self.model
                except Exception as e:
                    print(f"[ReorderService] heavy model load failed: {e}; falling back to lightweight scorer")
                    model = None
                    self.backend = None

            if self.backend == 'crossencoder' and model is not None:
                # 禁用梯度计算，提高推理性能
                with torch.no_grad():
                    scores = model.predict(pairs, batch_size=1)
                for doc, score in zip(documents, scores):
                    scored_documents.append({"document": doc, "similarity": float(score)})
                    print(f"[ReorderService] score: {float(score):.4f}")
            elif self.backend == 'inference_api':
                def _score_pair(q, d):
                    try:
                        text = f"{q}\n\n{d}"
                        res = self.api(text)
                        if isinstance(res, list) and res:
                            return float(res[0].get('score', 0.0))
                        elif isinstance(res, dict):
                            return float(res.get('score', 0.0))
                    except Exception as e:
                        print(f"InferenceApi scoring failed for a pair: {e}")
                    return 0.0
                scores = await asyncio.to_thread(lambda: [ _score_pair(q,d) for q,d in pairs ])
                for doc, score in zip(documents, scores):
                    scored_documents.append({"document": doc, "similarity": float(score)})
            else:
                # No heavyweight model available; use lightweight local scorer (token overlap Jaccard)
                def _tokens(text: str):
                    import re
                    return set(re.findall(r"\\w+", (text or '').lower()))
                q_tokens = _tokens(query)
                for doc in documents:
                    d_tokens = _tokens(doc)
                    if not q_tokens or not d_tokens:
                        score = 0.0
                    else:
                        inter = len(q_tokens & d_tokens)
                        union = len(q_tokens | d_tokens)
                        score = float(inter) / float(union) if union > 0 else 0.0
                    scored_documents.append({"document": doc, "similarity": float(score)})
                    print(f"[ReorderService:light] score: {score:.4f}")

            # 按相似度分数降序排序
            sorted_docs = sorted(scored_documents, key=lambda x: x["similarity"], reverse=True)
            print(f"[ReorderService] returning {len(sorted_docs)} documents")

            return {"success": True, "documents": sorted_docs, "error": ""}
        except Exception as e:
            error_msg = str(e)
            print(f"【重排序服务】重排序失败: {error_msg}")
            return {
                "success": False,
                "documents": [],
                "error": error_msg
            }

    @staticmethod
    async def format_reorder_result(sorted_docs: List[Dict]) -> str:
        """
        格式化重排序结果
        :param sorted_docs: 重排序后的文档列表
        :return: 格式化后的字符串
        """
        formatted_result = "重排序后的文档列表：\n"
        for i, doc in enumerate(sorted_docs, 1):
            formatted_result += f"{i}. 相似度: {doc.get('similarity', 0):.4f}\n"
            formatted_result += f"   内容: {doc.get('document', '')}\n\n"
        return formatted_result


# 全局重排序服务实例
reorder_service = ReorderService()
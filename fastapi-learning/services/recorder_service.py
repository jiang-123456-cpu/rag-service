import dashscope
from http import HTTPStatus
from typing import List, Dict, Any, Optional
from utils.config_handler import chroma_conf
from utils.path_tool import get_abs_path

class ReorderService:
    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        top_n: int = 1,
        instruct: Optional[str] = None
    ):
        config = chroma_conf or {}
        self.model = model or config.get("RERANK_MODEL", "qwen3-rerank")
        self.base_url = base_url or config.get("BASE_URL", "https://ws-cvofq7q3ca4iojsa.cn-beijing.maas.aliyuncs.com/api/v1")
        self.top_n = top_n
        self.instruct = instruct or "Given a web search query, retrieve relevant passages that answer the query."
        dashscope.base_http_api_url = self.base_url

    async def reorder_documents(
        self,
        query: str,
        documents: List[str]
    ) -> Dict[str, Any]:
        if not query or not documents:
            return {
                "success": False,
                "documents": [],
                "message": "Query or documents cannot be empty"
            }

        try:
            resp = dashscope.TextReRank.call(
                model=self.model,
                query=query,
                documents=documents,
                top_n=self.top_n,
                return_documents=True,
                instruct=self.instruct
            )

            if resp.status_code == HTTPStatus.OK:
                ranked_docs = []
                results = resp.output.get("results", [])
                for item in results:
                    # dashscope TextReRank 返回的 document 是 {"text": "..."} 字典，
                    # 兼容直接返回字符串的情况
                    raw_doc = item.get("document", "")
                    if isinstance(raw_doc, dict):
                        doc_text = raw_doc.get("text", "") or raw_doc.get("content", "")
                    else:
                        doc_text = raw_doc if isinstance(raw_doc, str) else str(raw_doc)
                    # 分数字段名为 relevance_score（部分版本为 score），兼容两者
                    ranked_docs.append({
                        "document": doc_text,
                        "similarity": item.get("relevance_score", item.get("score", 0.0)),
                        "index": item.get("index", -1)
                    })
                return {
                    "success": True,
                    "documents": ranked_docs,
                    "message": "Re-ranking completed successfully"
                }
            else:
                return {
                    "success": False,
                    "documents": [],
                    "message": f"API call failed with status code: {resp.status_code}, message: {resp.message}"
                }
        except Exception as e:
            return {
                "success": False,
                "documents": [],
                "message": f"Exception occurred during re-ranking: {str(e)}"
            }

reorder_service = ReorderService()
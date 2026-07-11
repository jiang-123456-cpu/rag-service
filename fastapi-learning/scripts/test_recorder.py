# -*- coding: utf-8 -*-
"""
scripts/test_recorder.py
简单的重排序模型测试脚本（可替换真实模型）
用法: python scripts/test_recorder.py
"""

import argparse
import math
import re
import os
import asyncio
from typing import List, Tuple, Callable

# Ensure project root on sys.path so 'services' can be imported when running script directly
import sys
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the project's ReorderService (uses sentence_transformers.CrossEncoder)
try:
    from services.recorder_service import reorder_service, ReorderService, check_and_download_reranker_model
except Exception:
    # If import fails, tests will still be able to use DummyReRanker/QwenReRanker fallback
    reorder_service = None



def tokenize(text: str) -> List[str]:
    return re.findall(r"\\w+", text.lower())


class DummyReRanker:
    """A trivial re-ranker that scores by token overlap with the query."""
    def score(self, query: str, doc: str) -> float:
        q = set(tokenize(query))
        d = set(tokenize(doc))
        if not q or not d:
            return 0.0
        return float(len(q & d)) / float(len(q | d))


class QwenReRanker:
    """Reranker wrapper for cross-encoder models like Qwen/Qwen3-Reranker-0.6B.

    Attempts to load via transformers locally (preferred). If that fails and a
    HF token is available, falls back to huggingface_hub.InferenceApi.
    Returns a float score in [0, 1] when possible.
    """
    def __init__(self, model_name: str = "Qwen/Qwen3-Reranker-0.6B", hf_token: str = None):
        self.model_name = model_name
        self.hf_token = hf_token or os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
        self.backend = None
        # Try transformers local load
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            import torch
            self.torch = torch
            self.tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.model.eval()
            self.backend = "transformers"
        except Exception as e:
            # Fallback to inference API
            try:
                from huggingface_hub import InferenceApi
                if not self.hf_token:
                    raise RuntimeError("HF token required for InferenceApi fallback; set HF_TOKEN env var or pass --hf-token")
                self.api = InferenceApi(repo_id=model_name, token=self.hf_token)
                self.backend = "inference_api"
            except Exception as e2:
                raise RuntimeError(f"Failed to load model locally ({e}) and failed InferenceApi fallback ({e2})")

    def score(self, query: str, doc: str) -> float:
        if self.backend == "transformers":
            inputs = self.tokenizer(query, doc, truncation=True, padding=True, return_tensors="pt")
            with self.torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                if logits is None:
                    return 0.0
                logits = logits.squeeze()
                # Handle various output shapes
                if logits.dim() == 0:
                    score = float(self.torch.sigmoid(logits).item())
                else:
                    num_labels = logits.shape[-1]
                    if num_labels == 1:
                        score = float(self.torch.sigmoid(logits).item())
                    elif num_labels == 2:
                        probs = self.torch.nn.functional.softmax(logits, dim=-1)
                        score = float(probs[1].item())
                    else:
                        probs = self.torch.nn.functional.softmax(logits, dim=-1)
                        score = float(probs.max().item())
                return score
        elif self.backend == "inference_api":
            # Use a simple concatenation; model-specific formatting may perform better
            text = f"{query}\n\n{doc}"
            res = self.api(inputs=text)
            if isinstance(res, list) and res:
                try:
                    return float(max(item.get("score", 0.0) for item in res))
                except Exception:
                    return float(res[0].get("score", 0.0))
            elif isinstance(res, dict):
                return float(res.get("score", 0.0))
            else:
                return 0.0
        else:
            raise RuntimeError("No backend available for QwenReRanker")


def rerank(reranker, query: str, candidates: List[str]) -> List[Tuple[int, float]]:
    scores = [(i, reranker.score(query, doc)) for i, doc in enumerate(candidates)]
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores


def dcg(rels: List[float], k: int) -> float:
    return sum((2**rel - 1) / math.log2(idx + 2) for idx, rel in enumerate(rels[:k]))


def ndcg_at_k(gold_rels: List[float], pred_ranking: List[int], k: int) -> float:
    pred_rels = [gold_rels[i] for i in pred_ranking[:k]]
    ideal_rels = sorted(gold_rels, reverse=True)
    idcg = dcg(ideal_rels, k)
    if idcg == 0:
        return 0.0
    return dcg(pred_rels, k) / idcg


def mrr_at_k(gold_rels: List[float], pred_ranking: List[int], k: int) -> float:
    for rank, idx in enumerate(pred_ranking[:k], start=1):
        if gold_rels[idx] > 0:
            return 1.0 / rank
    return 0.0


def evaluate(reranker, queries: List[str], candidates_list: List[List[str]], gold_list: List[List[float]], k: int = 10):
    ndcgs = []
    mrrs = []
    for q, cands, gold in zip(queries, candidates_list, gold_list):
        ranking = rerank(reranker, q, cands)
        pred_indices = [i for i, _ in ranking]
        ndcgs.append(ndcg_at_k(gold, pred_indices, k))
        mrrs.append(mrr_at_k(gold, pred_indices, k))
    return float(sum(ndcgs)) / len(ndcgs), float(sum(mrrs)) / len(mrrs)


async def evaluate_with_service(service, queries: List[str], candidates_list: List[List[str]], gold_list: List[List[float]], k: int = 10):
    """Evaluate using the async ReorderService from services/recorder_service.py
    service should expose an async method reorder_documents(query, documents) -> dict
    with keys: success(bool), documents: List[{'document': str, 'similarity': float}]
    """
    ndcgs = []
    mrrs = []
    for q, cands, gold in zip(queries, candidates_list, gold_list):
        res = await service.reorder_documents(q, cands)
        if not res.get("success", False):
            # fallback: treat as zero scores (keep original order)
            pred_indices = list(range(len(cands)))
        else:
            sorted_docs = res.get("documents", [])
            # Map sorted documents back to original indices (first-match)
            pred_indices = []
            used = [False] * len(cands)
            for item in sorted_docs:
                doc_text = item.get("document", "")
                # find first unused index
                found = False
                for i, orig in enumerate(cands):
                    if not used[i] and orig == doc_text:
                        pred_indices.append(i)
                        used[i] = True
                        found = True
                        break
                if not found:
                    # unknown document (maybe truncated) - skip
                    continue
            # append any missing originals at the end
            for i in range(len(cands)):
                if i not in pred_indices:
                    pred_indices.append(i)
        ndcgs.append(ndcg_at_k(gold, pred_indices, k))
        mrrs.append(mrr_at_k(gold, pred_indices, k))
    return float(sum(ndcgs)) / len(ndcgs), float(sum(mrrs)) / len(mrrs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--k', type=int, default=10, help='evaluate at K')
    parser.add_argument('--model', type=str, default='dummy', help='Reranker model id ("dummy" or HF model id like Qwen/Qwen3-Reranker-0.6B)')
    parser.add_argument('--hf-token', type=str, default=None, help='Hugging Face token for Inference API fallback')
    parser.add_argument('--use-service', action='store_true', help='Use services.recorder_service.ReorderService for scoring')
    args = parser.parse_args()

    # Example data: three queries, each with candidates and gold relevance (0/1 or graded)
    queries = [
        'python web framework',
        'best pizza near me',
        'how to tune a random forest model',
    ]

    candidates_list = [
        [
            'Flask is a lightweight Python web framework',
            'Django is a batteries-included framework for web development',
            'Learn JavaScript and React for frontend',
        ],
        [
            'Top 10 pizza places in town',
            'How to make pizza at home',
            'Local sushi restaurants and reviews',
        ],
        [
            'Random forest hyperparameters: n_estimators, max_depth',
            'A tutorial on linear regression',
            'Ensemble methods combine many models',
        ],
    ]

    # gold relevance aligned with candidate lists (graded relevance allowed)
    gold_list = [
        [1.0, 1.0, 0.0],
        [1.0, 0.0, 0.0],
        [1.0, 0.0, 0.5],
    ]

    # If requested, use the project's ReorderService which wraps CrossEncoder
    if args.use_service:
        if reorder_service is None:
            print('services.recorder_service not importable; falling back to DummyReRanker')
            reranker = DummyReRanker()
            ndcg, mrr = evaluate(reranker, queries, candidates_list, gold_list, k=args.k)
            print(f'Reranker: {reranker.__class__.__name__} | NDCG@{args.k}: {ndcg:.4f} | MRR@{args.k}: {mrr:.4f}')
        else:
            # Evaluate asynchronously using ReorderService; do not attempt automatic model download here
            ndcg, mrr = asyncio.run(evaluate_with_service(reorder_service, queries, candidates_list, gold_list, k=args.k))
            print(f'ReorderService | NDCG@{args.k}: {ndcg:.4f} | MRR@{args.k}: {mrr:.4f}')
    else:
        # Instantiate reranker based on requested model
        if args.model and args.model.lower() != 'dummy':
            try:
                reranker = QwenReRanker(model_name=args.model, hf_token=args.hf_token)
            except Exception as e:
                print(f'Failed to initialize {args.model}: {e}\nFalling back to DummyReRanker')
                reranker = DummyReRanker()
        else:
            reranker = DummyReRanker()

        ndcg, mrr = evaluate(reranker, queries, candidates_list, gold_list, k=args.k)
        print(f'Reranker: {reranker.__class__.__name__} | NDCG@{args.k}: {ndcg:.4f} | MRR@{args.k}: {mrr:.4f}')


if __name__ == '__main__':
    main()

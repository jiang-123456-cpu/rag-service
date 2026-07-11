from google.api.service_pb2 import Service
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableWithMessageHistory, RunnableLambda
from services.vector_service import VectorStore
from model.factory import chat_model, embed_model
from utils.prompt_loader import load_rag_prompts,load_system_prompts
from langchain_core.prompts import PromptTemplate
import asyncio

# 用户提问模板
USER_PROMPT = "{question}"

class RagService(object):
    def __init__(self):
        self.vector_store = VectorStore()
        self.chat_model = chat_model
        self.embeddings = embed_model



    def _format_docs(self, docs):
        """
        将检索到的文档格式化为上下文文本
        :param docs: 检索到的文档列表
        :return: 格式化后的文本
        """
        formatted = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get('file_path', '未知来源')
            formatted.append(f"[来源{i}: {source}]\n{doc.page_content}")
        return '\n\n'.join(formatted)
    def _extract_source_docs(self, docs):
        """
        提取参考文档来源信息
        :param docs: 检索到的文档列表
        :return: 来源信息列表
        """
        sources = []
        seen = set()
        for doc in docs:
            file_path = doc.metadata.get('file_path', '未知')
            if file_path not in seen:
                seen.add(file_path)
                sources.append({
                    'file_path': file_path,
                    'content': doc.page_content[:200]
                })
        return sources
    async def ask(self, query, kb_id, top_k: int = 5):
        """Retrieve, optionally re-rank, and run the RAG chain.

        Performs re-ranking after retrieval (if services.recorder_service.reorder_service is available).
        Keeps robust matching when mapping reordered texts back to original Document objects.
        """
        retriever = self.vector_store.get_retriever(kb_id)
        # retriever.invoke is blocking; run in thread to avoid blocking event loop
        docs = await asyncio.to_thread(retriever.invoke, query)
        if not docs:
            return '抱歉，在知识库中未找到与您问题相关的内容，请尝试换个方式提问。', []

        # Prepare candidate texts for re-ranking
        doc_texts = [d.page_content for d in docs]

        # Try to import reorder_service lazily to avoid hard dependency
        try:
            from services.recorder_service import reorder_service
        except Exception:
            reorder_service = None

        # If available, call reorder_service to re-rank retrieved docs
        if reorder_service is not None:
            try:
                # reorder_documents is async; await it
                rerank_res = await reorder_service.reorder_documents(query, doc_texts)
                if rerank_res.get('success', False):
                    ordered_items = rerank_res.get('documents', [])
                    new_docs = []
                    used = [False] * len(docs)
                    # Match ordered items back to original docs
                    for item in ordered_items:
                        text = item.get('document', '')
                        matched = False
                        # 1) exact match
                        for i, orig in enumerate(docs):
                            if not used[i] and orig.page_content == text:
                                new_docs.append(orig)
                                used[i] = True
                                matched = True
                                break
                        if matched:
                            continue
                        # 2) substring match
                        for i, orig in enumerate(docs):
                            if not used[i] and text and text in orig.page_content:
                                new_docs.append(orig)
                                used[i] = True
                                matched = True
                                break
                        if matched:
                            continue
                        # 3) try matching by metadata file_path if present in item.document text
                        for i, orig in enumerate(docs):
                            if not used[i]:
                                fp = orig.metadata.get('file_path') or ''
                                if fp and fp in text:
                                    new_docs.append(orig)
                                    used[i] = True
                                    matched = True
                                    break
                        # otherwise ignore this ordered item
                    # append any remaining originals preserving original order
                    for i, orig in enumerate(docs):
                        if not used[i]:
                            new_docs.append(orig)
                    docs = new_docs
                # if reorder failed or returned false, continue with original order
            except Exception:
                # swallow exceptions from re-ranking and continue with original docs
                pass

        # Trim to top_k for context
        docs_for_context = docs[:top_k]

        # 构建提示词
        prompt = ChatPromptTemplate.from_messages([
                ('system', load_system_prompts()),
                ('system', load_rag_prompts()),
                ('human', USER_PROMPT)
            ])

        rag_chain = (
            retriever
            | {
                'context': lambda x: self._format_docs(docs_for_context),
                'question': RunnablePassthrough()
            }
            | prompt
            | self.chat_model
            | StrOutputParser()
        )
        # rag_chain.invoke may be blocking; run in thread
        answer = await asyncio.to_thread(rag_chain.invoke, query)
        # 提取参考来源
        source_docs = self._extract_source_docs(docs_for_context)
        return answer, source_docs
from utils.config_handler import chroma_conf
from model.factory import embed_model
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_chroma import Chroma
from langchain_core.documents import Document
import os
from utils.file_handler import (
    get_file_md5_hex,
    check_md5_hex,
    save_md5_hex,
    get_file_documents,

)


class VectorStore:
    def __init__(self):
        self.vector_store = Chroma(
            collection_name="test_collection",
            embedding_function=embed_model,
            persist_directory=chroma_conf["persist_directory"]
        )
        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=chroma_conf["chunk_size"],
            chunk_overlap=chroma_conf["chunk_overlap"],
            separators=chroma_conf["separators"],
            length_function=len,
        )
    def _get_collection_name(self, kb_id):
        """
        根据知识库ID生成Chroma集合名称
        每个知识库使用独立的collection进行隔离
        """
        return f"kb_{kb_id}"
    def get_retriever(self, kb_id):
        """
        获取指定知识库的检索器
        :param kb_id: 知识库ID
        :return: Chroma检索器
        """
        collection_name = self._get_collection_name(kb_id)
        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=embed_model,
            persist_directory=chroma_conf["persist_directory"]
        )
        return vectorstore.as_retriever(
            search_kwargs={'k': chroma_conf["k"]}
        )

    def load_document(self,file_path,file_type,kb_id,doc_id):
          # 将扩展名补上点号，确保 endswith 能正确匹配
          dotted_types = tuple(
              f".{t.lstrip('.')}" if not t.startswith(".") else t
              for t in file_type
          )
          if not file_path.endswith(dotted_types):
            raise Exception("文件类型错误")
          md5_str = get_file_md5_hex(file_path)
          if check_md5_hex(md5_str):
            raise Exception("文件已存在")
          documents = get_file_documents(file_path)
          if not documents:
            raise Exception("文件为空")
          chunks = self.spliter.split_documents(documents)

          if not chunks:
            raise Exception("文件分块为空")
          # 将 metadata 和 id 设置到每个 Document 对象上
          for i, chunk in enumerate(chunks):
              chunk.metadata = {'doc_id': doc_id, 'file_path': file_path, 'chunk_index': i}
              chunk.id = f"doc_{doc_id}_chunk_{i}"
          vectorstore = Chroma(
              collection_name=self._get_collection_name(kb_id),
              embedding_function=embed_model,
              persist_directory=chroma_conf["persist_directory"]
          )
          vectorstore.add_documents(chunks)

          save_md5_hex(md5_str)
          return len(chunks)

    def delete_document(self, doc_id, kb_id):
        """
        从向量库中删除指定文档的所有分块
        :param doc_id: 文档ID
        :param kb_id: 知识库ID
        """
        collection_name = self._get_collection_name(kb_id)
        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=embed_model,
            persist_directory=chroma_conf["persist_directory"]
        )
        # 根据文档ID过滤并删除
        vectorstore._collection.delete(where={'doc_id': doc_id})









import os
import hashlib
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader,TextLoader
from utils.config_handler import chroma_conf
from utils.path_tool import get_abs_path

def get_file_md5_hex(filepath:str):  #获取文件的md5十六进制字符串
    if not os.path.exists(filepath):

        return
    if not os.path.isfile(filepath):
        return
    md5_obj=hashlib.md5()
    chunk_size=4096
    try:
        with open(filepath,"rb") as f:
            while chunk:= f.read(chunk_size):
                md5_obj.update(chunk)
            md5_hex=md5_obj.hexdigest()
            return md5_hex
    except Exception as e:
            return None

def check_md5_hex(md5_str: str):
    if not os.path.exists(get_abs_path(chroma_conf["md5_hex_store"])):
        open(get_abs_path(chroma_conf["md5_hex_store"]), "w", encoding="utf-8").close()
        return False
    with open(get_abs_path(chroma_conf["md5_hex_store"])) as f:
            for line in f.readlines():
                line = line.strip()
                if line == md5_str:
                   return True
    return False


def save_md5_hex(md5_str: str):
    with open(get_abs_path(chroma_conf["md5_hex_store"]), "a", encoding="utf-8") as f:
        f.write(md5_str + "\n")


def remove_md5_hex(md5_str: str):
    """从 md5.txt 中移除指定的 md5 字符串"""
    md5_file = get_abs_path(chroma_conf["md5_hex_store"])
    if not os.path.exists(md5_file):
        return
    with open(md5_file, "r", encoding="utf-8") as f:
        lines = [line for line in f.readlines() if line.strip() != md5_str]
    with open(md5_file, "w", encoding="utf-8") as f:
        f.writelines(lines)
def listdir_with_allowed_type(path:str,allowed_types:tuple[str]):
    files=[]
    if not os.path.isdir(path):

        return files
    for f in os.listdir(path):
        if f.endswith(allowed_types):
            files.append(os.path.join(path,f))
    return tuple(files)


def get_file_documents(read_path: str):
    """Return a list[Document] for the given file path.

    - For .txt and .pdf we delegate to existing loaders which should
      already return list[Document].
    - For .md we read the file as text and wrap it into a single Document.
    - For .docx we try to use python-docx to extract paragraphs; if
      python-docx isn't available or extraction fails we return an empty list
      (so the caller will skip the file).
    """
    # txt/pdf loaders are expected to return list[Document]
    if read_path.endswith("txt"):
        return txt_loader(read_path)
    if read_path.endswith("pdf"):
        return pdf_loader(read_path)

    # md -> read as UTF-8 text
    if read_path.endswith("md"):
        try:
            with open(get_abs_path(read_path), "r", encoding="utf-8") as f:
                content = f.read()
            return [Document(page_content=content, metadata={"source": read_path})]
        except Exception:
            return []

    # docx -> try python-docx dynamically
    if read_path.endswith("docx"):
        try:
            import importlib

            docx_mod = importlib.import_module("docx")
            DocxDocument = docx_mod.Document

            doc = DocxDocument(get_abs_path(read_path))
            paragraphs = [p.text for p in doc.paragraphs if p.text]
            content = "\n".join(paragraphs)
            return [Document(page_content=content, metadata={"source": read_path})]
        except Exception:
            # python-docx not installed or parsing failed
            return []

    return []
def pdf_loader(filepath:str,password=None)->list[Document]:
    return PyPDFLoader(filepath,password).load()
def txt_loader(filepath:str)->list[Document]:
    return TextLoader(filepath,encoding="utf-8").load()

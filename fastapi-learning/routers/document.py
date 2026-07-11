from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Depends
from db.database import get_db
import os
import uuid
from datetime import datetime
from utils.config_handler import chroma_conf
from schemas.document import DocumentUpload
from services.vector_service import VectorStore
from utils.file_handler import get_file_md5_hex, remove_md5_hex
router = APIRouter(prefix="/api/document", tags=["document"])

# upload directory and limits (can be configured in chroma_conf)
UPLOAD_DIR = chroma_conf.get("upload_folder", "uploads")
MAX_UPLOAD_MB = chroma_conf.get("max_upload_size_mb", 50)




def allowed_file(filename: str) -> bool:
    """判断文件扩展名是否在允许列表中"""
    allowed = chroma_conf.get("allow_knowledge_file_type") or chroma_conf.get("allowed_extensions")
    if not allowed:
        allowed = ["txt", "pdf", "md", "docx"]
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


# ---------------------------------------------------------------------------
# 获取文档列表（分页）
# ---------------------------------------------------------------------------
@router.get("/list")
async def get_list(
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(10, ge=1, le=100, description="每页数量"),
        kb_id: int = Query(None, description="知识库ID，不传则返回全部"),
):
    """
    获取文档列表（分页）
    - 传 kb_id：返回该知识库下的文档
    - 不传 kb_id：返回所有文档
    """
    offset = (page - 1) * page_size

    conn = get_db()
    cursor = conn.cursor()
    try:
        # ---------- 构建 WHERE 条件 ----------
        conditions = ["d.is_deleted = 0"]
        params: list = []

        if kb_id is not None:
            conditions.append("d.knowledge_base_id = %s")
            params.append(kb_id)

        where_clause = " WHERE " + " AND ".join(conditions)

        # ---------- 查询总数 ----------
        count_sql = f"""
            SELECT COUNT(*) AS total
            FROM knowledge_document d
            {where_clause}
        """
        cursor.execute(count_sql, params)
        total = cursor.fetchone()["total"]

        # ---------- 分页查询数据（JOIN 获取知识库名称）----------
        data_sql = f"""
            SELECT d.id, d.knowledge_base_id, kb.name AS kb_name,
                   d.file_name, d.file_path, d.file_size_kb,
                   d.file_size_kb AS file_size,
                   d.file_type,
                   d.chunk_count, d.status, d.uploaded_by, d.uploaded_at, d.updated_at
            FROM knowledge_document d
            LEFT JOIN knowledge_base kb ON d.knowledge_base_id = kb.id
            {where_clause}
            ORDER BY d.uploaded_at DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(data_sql, params + [page_size, offset])
        items = cursor.fetchall()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")
    finally:
        cursor.close()
        conn.close()


# ---------------------------------------------------------------------------
# 上传文档
# ---------------------------------------------------------------------------
@router.post("/upload")
async def upload_document(
    form: DocumentUpload = Depends(DocumentUpload.as_form),
    file: UploadFile = File(...),
):
    """
    上传文档并写入数据库
    - 验证文件扩展名
    - 用 UUID 重命名，避免文件名冲突
    - 将元数据插入 document 表
    """
    # 1. 校验文件名
    if not file.filename:
        raise HTTPException(status_code=400, detail="请选择要上传的文件")

    # 2. 校验文件类型
    if not allowed_file(file.filename):
        allowed = chroma_conf.get("allow_knowledge_file_type") or chroma_conf.get("allowed_extensions") or ["txt", "pdf", "md", "docx"]
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型，仅支持：{', '.join(sorted(allowed))}",
        )

    conn = get_db()
    cursor = conn.cursor()
    try:
        # 3. 检查知识库是否存在
        cursor.execute("SELECT id FROM knowledge_base WHERE id = %s AND is_deleted = 0", (form.kb_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="知识库不存在或已被删除")

        # 4. 生成唯一文件名并保存文件
        file_ext = file.filename.rsplit(".", 1)[1].lower()
        unique_name = f"{uuid.uuid4().hex}.{file_ext}"

        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(UPLOAD_DIR, unique_name)

        # read file content (streaming read could be used for large files)
        content = await file.read()

        # size check
        max_bytes = int(MAX_UPLOAD_MB) * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(status_code=400, detail=f"文件过大，最大允许 {MAX_UPLOAD_MB} MB")

        with open(file_path, "wb") as f:
            f.write(content)

        file_size = os.path.getsize(file_path)
        file_size_kb = round(file_size / 1024, 2)
        file_type = file_ext

        # 5. 插入文档记录
        sql = """
            INSERT INTO knowledge_document
                (knowledge_base_id, file_name, file_type, file_size_kb, chunk_count, status,
                 uploaded_by, uploaded_at, file_path, is_deleted)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(
            sql,
            (form.kb_id, file.filename, file_type, file_size_kb, 0, "pending",
             form.creator_id, datetime.now(), file_path, 0),
        )
        conn.commit()
        doc_id = cursor.lastrowid

        # 6. 向量化处理
        vector_service = VectorStore()
        chunk_count = vector_service.load_document(
            file_path, tuple(chroma_conf["allow_knowledge_file_type"]), form.kb_id, doc_id
        )

        # 7. 更新 chunk_count 和状态为 ready
        cursor.execute(
            "UPDATE knowledge_document SET chunk_count = %s, status = %s, updated_at = %s WHERE id = %s",
            (chunk_count, "ready", datetime.now(), doc_id),
        )

        # 8. 同步更新知识库的 document_count
        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM knowledge_document WHERE knowledge_base_id = %s AND is_deleted = 0",
            (form.kb_id,),
        )
        new_count = cursor.fetchone()["cnt"]
        cursor.execute(
            "UPDATE knowledge_base SET document_count = %s WHERE id = %s",
            (new_count, form.kb_id),
        )
        conn.commit()
        return {
            "message": "上传成功",
            "data": {
                "id": doc_id,
                "kb_id": form.kb_id,
                "file_name": file.filename,
                "file_path": file_path,
                "file_size": file_size,
                "file_type": file_type,
                "status": "pending",
            },
        }

    except HTTPException:
        # 向上抛出已有的 HTTP 异常（如知识库不存在）
        raise
    except Exception as e:
        conn.rollback()
        # 若 DB 写入失败，尝试清理已保存的文件
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")
    finally:
        cursor.close()
        conn.close()


# ---------------------------------------------------------------------------
# 删除文档
# ---------------------------------------------------------------------------
@router.post("/delete")
async def delete_document(doc_id: int = Query(..., description="文档ID")):
    """
    删除文档（管理员操作）
    - 删除数据库记录
    - 删除对应的物理文件
    - 同步更新知识库的 document_count
    """
    conn = get_db()
    cursor = conn.cursor()
    try:
        # 1. 查询文档信息
        cursor.execute(
            "SELECT id, knowledge_base_id, file_path, status FROM knowledge_document WHERE id = %s AND is_deleted = 0",
            (doc_id,),
        )
        doc = cursor.fetchone()
        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")

        kb_id = doc["knowledge_base_id"]
        file_path = doc["file_path"]

        # 2. 删除文件前计算 MD5，并从 md5.txt 中移除
        if file_path and os.path.exists(file_path):
            md5_str = get_file_md5_hex(file_path)
            if md5_str:
                remove_md5_hex(md5_str)
            os.remove(file_path)

        # 3. 软删除数据库记录（设置 is_deleted = 1）
        cursor.execute(
            "UPDATE knowledge_document SET is_deleted = 1, updated_at = %s WHERE id = %s",
            (datetime.now(), doc_id),
        )

        # 4. 更新知识库的 document_count（统计剩余未删除文档数）
        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM knowledge_document WHERE knowledge_base_id = %s AND is_deleted = 0",
            (kb_id,),
        )
        new_count = cursor.fetchone()["cnt"]

        cursor.execute(
            "UPDATE knowledge_base SET document_count = %s WHERE id = %s",
            (new_count, kb_id),
        )

        conn.commit()
        vector_service = VectorStore()
        vector_service.delete_document(doc_id, kb_id)
        return {"message": "删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
    finally:
        cursor.close()
        conn.close()

from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from db.database import get_db
from db.models import KnowledgeDocument, KnowledgeBase as KBModel, Users, UserRole
import os
import uuid
from datetime import datetime
from utils.config_handler import chroma_conf
from schemas.document import DocumentUpload
from services.vector_service import VectorStore
from utils.file_handler import get_file_md5_hex, remove_md5_hex
from utils.auth import get_current_user, require_role

router = APIRouter(prefix="/api/document", tags=["document"])

UPLOAD_DIR = chroma_conf.get("upload_folder", "uploads")
MAX_UPLOAD_MB = chroma_conf.get("max_upload_size_mb", 50)


def allowed_file(filename: str) -> bool:
    allowed = chroma_conf.get("allow_knowledge_file_type") or chroma_conf.get("allowed_extensions")
    if not allowed:
        allowed = ["txt", "pdf", "md", "docx"]
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


@router.get("/list")
async def get_list(
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(10, ge=1, le=100, description="每页数量"),
        kb_id: int = Query(None, description="知识库ID，不传则返回全部"),
        db: AsyncSession = Depends(get_db),
        current_user: Users = Depends(get_current_user),
):
    offset = (page - 1) * page_size
    try:
        count_stmt = select(func.count(KnowledgeDocument.id)).where(KnowledgeDocument.is_deleted == 0)
        if kb_id is not None:
            count_stmt = count_stmt.where(KnowledgeDocument.knowledge_base_id == kb_id)
        total = (await db.execute(count_stmt)).scalar()

        doc_stmt = (
            select(KnowledgeDocument, KBModel.name.label("kb_name"))
            .outerjoin(KBModel, KnowledgeDocument.knowledge_base_id == KBModel.id)
            .where(KnowledgeDocument.is_deleted == 0)
        )
        if kb_id is not None:
            doc_stmt = doc_stmt.where(KnowledgeDocument.knowledge_base_id == kb_id)

        docs = (
            await db.execute(
                doc_stmt
                .order_by(KnowledgeDocument.uploaded_at.desc())
                .offset(offset)
                .limit(page_size)
            )
        ).all()

        items = []
        for doc, kb_name in docs:
            items.append({
                "id": doc.id,
                "knowledge_base_id": doc.knowledge_base_id,
                "kb_name": kb_name,
                "file_name": doc.file_name,
                "file_path": doc.file_path,
                "file_size_kb": float(doc.file_size_kb) if doc.file_size_kb is not None else 0,
                "file_size": float(doc.file_size_kb) if doc.file_size_kb is not None else 0,
                "file_type": doc.file_type,
                "chunk_count": doc.chunk_count,
                "status": doc.status,
                "uploaded_by": doc.uploaded_by,
                "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
            })

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.post("/upload")
async def upload_document(
    form: DocumentUpload = Depends(DocumentUpload.as_form),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="请选择要上传的文件")

    if not allowed_file(file.filename):
        allowed = chroma_conf.get("allow_knowledge_file_type") or chroma_conf.get("allowed_extensions") or ["txt", "pdf", "md", "docx"]
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型，仅支持：{', '.join(sorted(allowed))}",
        )

    db_doc = None
    file_path = None
    try:
        result = await db.execute(
            select(KBModel).where(KBModel.id == form.kb_id, KBModel.is_deleted == 0)
        )
        kb = result.scalar_one_or_none()
        if not kb:
            raise HTTPException(status_code=404, detail="知识库不存在或已被删除")

        file_ext = file.filename.rsplit(".", 1)[1].lower()
        unique_name = f"{uuid.uuid4().hex}.{file_ext}"

        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(UPLOAD_DIR, unique_name)

        content = await file.read()

        max_bytes = int(MAX_UPLOAD_MB) * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(status_code=400, detail=f"文件过大，最大允许 {MAX_UPLOAD_MB} MB")

        with open(file_path, "wb") as f:
            f.write(content)

        file_size = os.path.getsize(file_path)
        file_size_kb = round(file_size / 1024, 2)
        file_type = file_ext

        db_doc = KnowledgeDocument(
            knowledge_base_id=form.kb_id,
            file_name=file.filename,
            file_type=file_type,
            file_size_kb=file_size_kb,
            chunk_count=0,
            status="pending",
            uploaded_by=current_user.username,
            uploaded_at=datetime.now(),
            file_path=file_path,
            is_deleted=0,
        )
        db.add(db_doc)
        await db.commit()
        await db.refresh(db_doc)
        doc_id = db_doc.id

        vector_service = VectorStore()
        chunk_count = vector_service.load_document(
            file_path, tuple(chroma_conf["allow_knowledge_file_type"]), form.kb_id, doc_id
        )

        db_doc.chunk_count = chunk_count
        db_doc.status = "ready"
        db_doc.updated_at = datetime.now()

        count_result = await db.execute(
            select(func.count(KnowledgeDocument.id)).filter(
                KnowledgeDocument.knowledge_base_id == form.kb_id,
                KnowledgeDocument.is_deleted == 0,
            )
        )
        new_count = count_result.scalar()
        kb.document_count = new_count
        await db.commit()
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
        raise
    except Exception as e:
        await db.rollback()
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/delete")
async def delete_document(
    doc_id: int = Query(..., description="文档ID"),
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(require_role(UserRole.ADMIN)),
):
    try:
        result = await db.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id, KnowledgeDocument.is_deleted == 0)
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")

        kb_id = doc.knowledge_base_id
        file_path = doc.file_path

        if file_path and os.path.exists(file_path):
            md5_str = get_file_md5_hex(file_path)
            if md5_str:
                remove_md5_hex(md5_str)
            os.remove(file_path)

        doc.is_deleted = 1
        doc.updated_at = datetime.now()

        count_result = await db.execute(
            select(func.count(KnowledgeDocument.id)).filter(
                KnowledgeDocument.knowledge_base_id == kb_id,
                KnowledgeDocument.is_deleted == 0,
            )
        )
        new_count = count_result.scalar()
        kb_result = await db.execute(select(KBModel).where(KBModel.id == kb_id))
        kb = kb_result.scalar_one_or_none()
        if kb:
            kb.document_count = new_count

        await db.commit()
        vector_service = VectorStore()
        vector_service.delete_document(doc_id, kb_id)
        return {"message": "删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
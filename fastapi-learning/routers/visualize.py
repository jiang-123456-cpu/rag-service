from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from db.database import get_db
from db.models import KnowledgeDocument, KnowledgeBase

router = APIRouter(prefix="/api/visualize", tags=["visualize"])

@router.get("/amount")
async def get_amount(
        db_session: AsyncSession = Depends(get_db),
):
    try:
        base_count = await db_session.execute(
            select(func.count(KnowledgeBase.id)).where(KnowledgeBase.is_deleted == 0)
        )
        doc_count = await db_session.execute(
            select(func.count(KnowledgeDocument.id)).where(KnowledgeDocument.is_deleted == 0)
        )
        return {
            "knowledge_bases": base_count.scalar(),
            "documents": doc_count.scalar()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")
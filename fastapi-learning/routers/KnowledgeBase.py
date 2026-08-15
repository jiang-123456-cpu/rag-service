from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.KnowledgeBase import KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseDelete
from db.database import get_db
from db.models import KnowledgeBase as KBModel, Users, UserRole
from datetime import datetime
from utils.auth import get_current_user, require_role
from sqlalchemy import select, func

router = APIRouter(prefix="/api/knowledgebase", tags=["knowledgebase"])


@router.post("/create")
async def create_knowledgebase(
    knowledgebase: KnowledgeBaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    try:
        new_kb = KBModel(
            name=knowledgebase.name,
            description=knowledgebase.description,
            document_count=0,
            creator_username=current_user.username,
            created_at=datetime.now(),
            is_deleted=0,
        )
        db.add(new_kb)
        await db.commit()
        await db.refresh(new_kb)
        return {
            "message": "Knowledge base created successfully",
            "id": new_kb.id,
            "name": new_kb.name,
            "description": new_kb.description,
            "document_count": new_kb.document_count,
            "creator_username": new_kb.creator_username,
            "created_at": new_kb.created_at.isoformat() if new_kb.created_at else None,
            "is_deleted": new_kb.is_deleted,
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.post("/update")
async def update_knowledgebase(
    kb: KnowledgeBaseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    try:
        result = await db.execute(
            select(KBModel).where(KBModel.id == kb.id, KBModel.is_deleted == 0)
        )
        db_kb = result.scalar_one_or_none()
        if not db_kb:
            raise HTTPException(status_code=404, detail="知识库不存在")

        updated = False
        if kb.name is not None:
            db_kb.name = kb.name
            updated = True
        if kb.description is not None:
            db_kb.description = kb.description
            updated = True

        if not updated:
            raise HTTPException(status_code=400, detail="没有提供需要更新的字段")

        db_kb.updated_at = datetime.now()
        await db.commit()
        return {"message": "Knowledge base updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.post("/delete")
async def delete_knowledgebase(
    kb: KnowledgeBaseDelete,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(require_role(UserRole.ADMIN)),
):
    try:
        result = await db.execute(
            select(KBModel).where(KBModel.id == kb.id, KBModel.is_deleted == 0)
        )
        db_kb = result.scalar_one_or_none()
        if not db_kb:
            raise HTTPException(status_code=404, detail="知识库不存在")

        db_kb.is_deleted = 1
        db_kb.updated_at = datetime.now()
        await db.commit()
        return {"message": "Knowledge base deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.get("/")
async def list_knowledge_bases(
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(10, ge=1, le=100, description="每页数量"),
        db: AsyncSession = Depends(get_db),
        current_user: Users = Depends(get_current_user),
):
    offset = (page - 1) * page_size
    try:
        count_result = await db.execute(
            select(func.count(KBModel.id)).where(KBModel.is_deleted == 0)
        )
        total = count_result.scalar()

        kb_list = (
            await db.execute(
                select(KBModel)
                .where(KBModel.is_deleted == 0)
                .order_by(KBModel.id.desc())
                .offset(offset)
                .limit(page_size)
            )
        ).scalars().all()

        items = []
        for kb in kb_list:
            items.append({
                "id": kb.id,
                "name": kb.name,
                "description": kb.description,
                "document_count": kb.document_count,
                "creator_username": kb.creator_username,
                "created_at": kb.created_at.isoformat() if kb.created_at else None,
                "updated_at": kb.updated_at.isoformat() if kb.updated_at else None,
            })

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")
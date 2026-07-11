from fastapi import APIRouter, HTTPException, Query
from schemas.KnowledgeBase import KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseDelete
from db.database import get_db
from datetime import datetime
router = APIRouter(prefix="/api/knowledgebase", tags=["knowledgebase"])

@router.post("/create")
async def create_knowledgebase(knowledgebase: KnowledgeBaseCreate):
    conn = get_db()
    cursor = conn.cursor()
    try:
        sql = """
                INSERT INTO knowledge_base (name, description,document_count,creator_username,created_at,is_deleted)
                VALUES (%s,%s,%s,%s,%s,%s)
            """
        cursor.execute(sql, (knowledgebase.name, knowledgebase.description,0,"系统管理员",datetime.now(),0))
        conn.commit()
        return {"message": "Knowledge base created successfully",
                "id": cursor.lastrowid,
                "name": knowledgebase.name,
                "description": knowledgebase.description,
                "document_count": 0,
                "creator_username": "系统管理员",
                "created_at": datetime.now(),
                "is_deleted": 0
                }
    except Exception as e:
        conn.rollback()
        return {"error": str(e)}
    finally:
        cursor.close()
        conn.close()

@router.post("/update")
async def update_knowledgebase(kb: KnowledgeBaseUpdate):
    conn = get_db()
    cursor = conn.cursor()
    try:
        updates = []
        params = []
        if kb.name is not None:
            updates.append("name = %s")
            params.append(kb.name)
        if kb.description is not None:
            updates.append("description = %s")
            params.append(kb.description)

        if not updates:
            raise HTTPException(status_code=400, detail="没有提供需要更新的字段")

        sql = f"UPDATE knowledge_base SET {', '.join(updates)} WHERE id = %s"
        params.append(kb.id)
        cursor.execute(sql, params)
        conn.commit()
        return {"message": "Knowledge base updated successfully"}
    except Exception as e:
        conn.rollback()
        return {"error": str(e)}
    finally:
        cursor.close()
        conn.close()

@router.post("/delete")
async def delete_knowledgebase(kb: KnowledgeBaseDelete):
    conn = get_db()
    cursor = conn.cursor()
    try:
        sql = "DELETE FROM knowledge_base WHERE id = %s"
        cursor.execute(sql, (kb.id,))
        conn.commit()
        return {"message": "Knowledge base deleted successfully"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        cursor.close()
        conn.close()

@router.get("/")
async def list_knowledge_bases(
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(10, ge=1, le=100, description="每页数量")
):
    """
    查询知识库列表（未软删除的）
    返回分页数据及总数
    """
    offset = (page - 1) * page_size

    conn = get_db()
    cursor = conn.cursor()
    try:
        # 查询总数
        cursor.execute("SELECT COUNT(*) AS total FROM knowledge_base WHERE is_deleted = 0")
        total = cursor.fetchone()["total"]

        # 分页查询数据
        sql = """
            SELECT id, name, description, document_count, creator_username, created_at, updated_at
            FROM knowledge_base
            WHERE is_deleted = 0
            ORDER BY id DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(sql, (page_size, offset))
        items = cursor.fetchall()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")
    finally:
        cursor.close()
        conn.close()


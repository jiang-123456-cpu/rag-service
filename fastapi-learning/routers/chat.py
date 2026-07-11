from fastapi import APIRouter, HTTPException, Query, Depends
from db.database import get_db
from schemas.chat import ChatRequest
from services.rag_service import RagService
from datetime import datetime

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("/ask")
async def ask_chat(data: ChatRequest):
    if not data:
        raise HTTPException(status_code=400, detail='Invalid request data')
    if not data.question:
        raise HTTPException(status_code=400, detail='Question is required')
    if not data.kb_id:
        raise HTTPException(status_code=400, detail='Knowledge base ID is required')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("select id,name from knowledge_base where id = %s", (data.kb_id,))
    kb_row = cursor.fetchone()
    if not kb_row:
        raise HTTPException(status_code=404, detail='Knowledge base not found')
    kb_name = kb_row['name']
    try:
       rag_service = RagService()
       answer, sources = await rag_service.ask(data.question, data.kb_id)
       cursor.execute("insert into conversation_history (question, answer, knowledge_base, questioner, create_time, operation) values (%s, %s, %s, %s, %s, %s)", (data.question, answer, kb_name, "系统管理员", datetime.now(), "ask"))
       conn.commit()
       return {"answer": answer, "sources": sources}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def get_chat_list(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1),
        kb_id: int = Query(None, ge=1)
):
    conn = get_db()
    cursor = conn.cursor()
    try:
        offset = (page - 1) * page_size

        if kb_id is not None:
            # 根据 kb_id 查出知识库名称，再按名称筛选对话记录
            cursor.execute(
                "SELECT name FROM knowledge_base WHERE id = %s",
                (kb_id,)
            )
            kb_row = cursor.fetchone()
            if not kb_row:
                raise HTTPException(status_code=404, detail='知识库不存在')
            kb_name = kb_row['name']

            cursor.execute(
                "SELECT COUNT(*) AS total FROM conversation_history WHERE knowledge_base = %s",
                (kb_name,)
            )
            total = cursor.fetchone()['total']

            cursor.execute(
                "SELECT id, question, answer, knowledge_base, questioner, create_time, operation "
                "FROM conversation_history WHERE knowledge_base = %s "
                "ORDER BY create_time DESC LIMIT %s OFFSET %s",
                (kb_name, page_size, offset)
            )
        else:
            # 不传 kb_id 时展示全部数据
            cursor.execute(
                "SELECT COUNT(*) AS total FROM conversation_history"
            )
            total = cursor.fetchone()['total']

            cursor.execute(
                "SELECT id, question, answer, knowledge_base, questioner, create_time, operation "
                "FROM conversation_history "
                "ORDER BY create_time DESC LIMIT %s OFFSET %s",
                (page_size, offset)
            )

        items = cursor.fetchall()
        return {"total": total, "items": items}
    finally:
        cursor.close()
        conn.close()







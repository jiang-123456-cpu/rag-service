from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from db.models import ConversationHistory, KnowledgeBase as KBModel, Users
from schemas.chat import ChatRequest
from services.rag_service import RagService
from datetime import datetime
from utils.auth import get_current_user
from sqlalchemy import select, func
from langchain_core.messages import HumanMessage
from agent.agent import get_agent_factory
from utils.prompt_loader import load_system_prompts, load_rag_prompts
import json
import asyncio

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _build_rag_system_prompt(context: str) -> str:
	system_part = load_system_prompts()
	rag_part = load_rag_prompts()
	return f"{system_part}\n\n{rag_part}\n\n以下是检索到的上下文：\n{context}"


@router.post("/ask")
async def ask_chat(
	data: ChatRequest,
	db: AsyncSession = Depends(get_db),
	current_user: Users = Depends(get_current_user),
):
	if not data:
		raise HTTPException(status_code=400, detail="Invalid request data")
	if not data.question:
		raise HTTPException(status_code=400, detail="Question is required")
	if not data.kb_id:
		raise HTTPException(status_code=400, detail="Knowledge base ID is required")

	kb_result = await db.execute(select(KBModel).where(KBModel.id == data.kb_id))
	kb_row = kb_result.scalar_one_or_none()
	if not kb_row:
		raise HTTPException(status_code=404, detail="Knowledge base not found")
	kb_name = kb_row.name

	try:
		rag_service = RagService()
		retriever = rag_service.vector_store.get_retriever(data.kb_id)
		docs = await asyncio.to_thread(retriever.invoke, data.question)

		sources = []
		if docs:
			seen = set()
			for doc in docs:
				file_path = doc.metadata.get("file_path", "未知")
				if file_path not in seen:
					seen.add(file_path)
					sources.append({
						"file_path": file_path,
						"content": doc.page_content[:200]
					})

		# 如果未检索到任何文档，使用 rag_service.ask 返回原始友好提示（保持旧逻辑）
		if not docs:
			answer, sources = await rag_service.ask(data.question, data.kb_id)

			async def event_generator_empty():
				try:
					yield json.dumps({"type": "sources", "data": sources}, ensure_ascii=False) + "\n"
					yield json.dumps({"type": "content", "data": answer}, ensure_ascii=False) + "\n"
					try:
						history = ConversationHistory(
							question=data.question,
							answer=answer,
							knowledge_base=kb_name,
							questioner=current_user.username,
							create_time=datetime.now(),
							operation="ask",
						)
						db.add(history)
						await db.commit()
					except Exception:
						await db.rollback()
					yield json.dumps({"type": "done", "data": None}, ensure_ascii=False) + "\n"
				except Exception as e:
					yield json.dumps({"type": "error", "data": str(e)}, ensure_ascii=False) + "\n"

			return StreamingResponse(
				event_generator_empty(),
				media_type="text/event-stream",
				headers={
					"Cache-Control": "no-cache",
					"Connection": "keep-alive",
					"X-Accel-Buffering": "no",
				}
			)

		context = rag_service._format_docs(docs[:5]) if docs else "未找到相关上下文"
		system_prompt = _build_rag_system_prompt(context)

		agent_factory = get_agent_factory()
		messages = [HumanMessage(content=data.question)]
		thread_id = data.session_id or f"session-{current_user.id}-{data.kb_id}"

		full_answer = []

		async def event_generator():
			try:
				yield json.dumps({"type": "sources", "data": sources}, ensure_ascii=False) + "\n"
				async for chunk in agent_factory.astream_content(
					messages=messages,
					system_prompt=system_prompt,
					thread_id=thread_id,
				):
					full_answer.append(chunk)
					yield json.dumps({"type": "content", "data": chunk}, ensure_ascii=False) + "\n"

				final_answer = "".join(full_answer)
				try:
					history = ConversationHistory(
						question=data.question,
						answer=final_answer,
						knowledge_base=kb_name,
						questioner=current_user.username,
						create_time=datetime.now(),
						operation="ask",
					)
					db.add(history)
					await db.commit()
				except Exception:
					await db.rollback()
				yield json.dumps({"type": "done", "data": None}, ensure_ascii=False) + "\n"
			except Exception as e:
				yield json.dumps({"type": "error", "data": str(e)}, ensure_ascii=False) + "\n"

		return StreamingResponse(
			event_generator(),
			media_type="text/event-stream",
			headers={
				"Cache-Control": "no-cache",
				"Connection": "keep-alive",
				"X-Accel-Buffering": "no",
			}
		)
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def get_chat_list(
		page: int = Query(1, ge=1),
		page_size: int = Query(10, ge=1),
		kb_id: int = Query(None, ge=1),
		db: AsyncSession = Depends(get_db),
		current_user: Users = Depends(get_current_user),
):
	try:
		offset = (page - 1) * page_size

		if kb_id is not None:
			kb_result = await db.execute(select(KBModel).where(KBModel.id == kb_id))
			kb_row = kb_result.scalar_one_or_none()
			if not kb_row:
				raise HTTPException(status_code=404, detail="知识库不存在")
			kb_name = kb_row.name

			count_result = await db.execute(
				select(func.count(ConversationHistory.id)).where(
					ConversationHistory.knowledge_base == kb_name
				)
			)
			total = count_result.scalar()

			history_list = (
				await db.execute(
					select(ConversationHistory)
					.where(ConversationHistory.knowledge_base == kb_name)
					.order_by(ConversationHistory.create_time.desc())
					.offset(offset)
					.limit(page_size)
				)
			).scalars().all()
		else:
			count_result = await db.execute(select(func.count(ConversationHistory.id)))
			total = count_result.scalar()

			history_list = (
				await db.execute(
					select(ConversationHistory)
					.order_by(ConversationHistory.create_time.desc())
					.offset(offset)
					.limit(page_size)
				)
			).scalars().all()

		items = []
		for h in history_list:
			items.append({
				"id": h.id,
				"question": h.question,
				"answer": h.answer,
				"knowledge_base": h.knowledge_base,
				"questioner": h.questioner,
				"create_time": h.create_time.isoformat() if h.create_time else None,
				"operation": h.operation,
			})

		return {"total": total, "items": items}
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))

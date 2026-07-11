from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List

from datetime import datetime






class ChatRequest(BaseModel):
	"""请求模型：用于 AI 问答接口的入参。

	字段：
	- question: 用户提问文本（必填）
	- kb_id: 知识库 ID，用来限定检索范围（必填，>=1）
	- session_id: 会话 ID（可选），用于多轮上下文追踪
	"""

	question: str = Field(..., min_length=1, description="用户问题文本")
	kb_id: int = Field(..., ge=1, description="知识库 ID（>=1）")
	session_id: Optional[str] = Field(None, description="会话 ID，可选，用于多轮对话")

	class Config:
		schema_extra = {
			"example": {
				"question": "如何配置项目的 Chroma 向量库？",
				"kb_id": 1,
				"session_id": "sess-abc123",
			}
		}


class ChatHistory(BaseModel):
	id: int = Field(..., description="会话历史记录的 ID")
	question: str = Field(..., description="用户问题文本")
	answer: str = Field(..., description="AI 回答文本")
	knowledge_base: Optional[str] = Field(None, description="知识库名称")
	questioner: str = Field(..., description="用户名称")
	create_time: datetime = Field(..., description="会话历史记录的创建时间")
	operation: Optional[str] = Field(None, description="操作类型")

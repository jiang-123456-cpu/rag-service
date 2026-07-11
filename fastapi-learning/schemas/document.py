from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import Form
from typing import Optional
from enum import Enum
from decimal import Decimal
from datetime import datetime


class FileType(str, Enum):
	MD = "MD"
	DOCX = "DOCX"
	TXT = "TXT"
	PDF = "PDF"
	OTHER = "OTHER"


class DocumentStatus(str, Enum):
	PROCESSING = "processing"
	READY = "ready"
	FAILED = "failed"


class DocumentBase(BaseModel):
	knowledge_base_id: int = Field(..., ge=1, description="所属知识库ID，关联 knowledge_base.id")
	file_name: str = Field(..., max_length=255, description="文件名（含扩展名）")
	file_type: FileType = Field(..., description="文件类型/扩展名，例如 MD、DOCX、TXT、PDF")
	file_size_kb: Decimal = Field(..., ge=0, description="文件大小，单位KB，支持小数")
	chunk_count: int = Field(..., ge=0, description="分块数（文档被切分的块数）")
	status: DocumentStatus = Field(DocumentStatus.READY, description="文档处理状态")
	uploaded_by: Optional[str] = Field(None, max_length=50, description="上传者用户名")
	uploaded_at: Optional[datetime] = Field(None, description="上传时间")
	file_path: Optional[str] = Field(None, max_length=500, description="文件存储路径（相对或绝对）")
	file_hash: Optional[str] = Field(None, max_length=64, description="文件哈希值（用于去重校验）")
	updated_at: Optional[datetime] = Field(None, description="最后更新时间")
	is_deleted: int = Field(0, ge=0, le=1, description="软删除标志，0-未删除，1-已删除")

	class Config:
		# allow population by field name even if enums used
		use_enum_values = True


class DocumentCreate(DocumentBase):
	"""用于创建/上传文档的入参模型。"""


class DocumentUpload(BaseModel):
	"""用于接收上传表单中的非文件字段（可与 FastAPI 的 UploadFile 一起使用）。

	使用示例（在路由中以依赖注入或直接调用）：
	@router.post('/upload')
	async def upload(form: DocumentUpload = Depends(DocumentUpload.as_form), file: UploadFile = File(...)):
		# form.kb_id, form.creator_id 可用
		...
	"""

	kb_id: int = Field(..., ge=1, description="所属知识库ID，必须 >= 1")
	creator_id: Optional[int] = Field(None, ge=0, description="上传者用户ID，可选")

	@classmethod
	def as_form(
		cls,
		kb_id: int = Form(..., description="知识库ID"),
		creator_id: Optional[int] = Form(None, description="上传者用户ID"),
	) -> "DocumentUpload":
		return cls(kb_id=kb_id, creator_id=creator_id)


class DocumentUploadResponse(BaseModel):
	id: int
	kb_id: int
	file_name: str
	file_path: Optional[str] = None
	file_size_kb: Optional[Decimal] = None
	status: DocumentStatus
	message: Optional[str] = None


class DocumentUpdate(BaseModel):
	"""用于部分更新的模型：只包含允许更新的字段。"""
	file_name: Optional[str] = Field(None, max_length=255)
	file_type: Optional[FileType] = None
	file_size_kb: Optional[Decimal] = Field(None, ge=0)
	chunk_count: Optional[int] = Field(None, ge=0)
	status: Optional[DocumentStatus] = None
	file_path: Optional[str] = Field(None, max_length=500)
	file_hash: Optional[str] = Field(None, max_length=64)
	is_deleted: Optional[int] = Field(None, ge=0, le=1)


class DocumentInDB(DocumentBase):
	id: int = Field(..., ge=1, description="文档ID 主键")

	@classmethod
	def from_db_row(cls, row: dict) -> "DocumentInDB":
		"""将 pymysql 返回的 dict row 转换为 DocumentInDB 实例。

		示例 row 字段与数据库列名一致：id, knowledge_base_id, file_name, file_type, file_size_kb,
		chunk_count, status, uploaded_by, uploaded_at, file_path, file_hash, updated_at, is_deleted
		"""
		# 某些数据库驱动会返回 Decimal/bytes 等类型，Pydantic 会尝试转换
		data = {
			"id": row.get("id"),
			"knowledge_base_id": row.get("knowledge_base_id"),
			"file_name": row.get("file_name"),
			"file_type": row.get("file_type") if row.get("file_type") is not None else FileType.OTHER,
			"file_size_kb": row.get("file_size_kb"),
			"chunk_count": row.get("chunk_count"),
			"status": row.get("status") if row.get("status") is not None else DocumentStatus.READY,
			"uploaded_by": row.get("uploaded_by"),
			"uploaded_at": row.get("uploaded_at"),
			"file_path": row.get("file_path"),
			"file_hash": row.get("file_hash"),
			"updated_at": row.get("updated_at"),
			"is_deleted": row.get("is_deleted", 0),
		}
		return cls(**data)


# ---------- SQL 建表建议（MySQL） ----------
# CREATE TABLE `documents` (
#   `id` int NOT NULL AUTO_INCREMENT,
#   `knowledge_base_id` int NOT NULL,
#   `file_name` varchar(255) NOT NULL,
#   `file_type` varchar(50) DEFAULT NULL,
#   `file_size_kb` decimal(10,2) DEFAULT NULL,
#   `chunk_count` int DEFAULT 0,
#   `status` varchar(20) DEFAULT 'ready',
#   `uploaded_by` varchar(50) DEFAULT NULL,
#   `uploaded_at` datetime DEFAULT NULL,
#   `file_path` varchar(500) DEFAULT NULL,
#   `file_hash` varchar(64) DEFAULT NULL,
#   `updated_at` datetime DEFAULT NULL,
#   `is_deleted` tinyint(1) NOT NULL DEFAULT 0,
#   PRIMARY KEY (`id`),
#   INDEX `idx_kb_id` (`knowledge_base_id`),
#   INDEX `idx_file_hash` (`file_hash`)
# ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

# 建议：
# - knowledge_base_id 建索引用于按知识库分页/过滤
# - file_hash 建唯一索引或普通索引用于去重检测（视业务而定）
# - status 使用枚举值限制写入范围，有助于查询过滤


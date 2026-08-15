# ""
# SQLAlchemy ORM 模型
# 对应数据库 backend 中的 4 张表：
#   - users               用户表
#   - knowledge_base      知识库表
#   - knowledge_document  知识库文档表
#   - conversation_history 对话历史表
# """

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    Enum,
    SmallInteger,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.mysql import DECIMAL
from sqlalchemy.sql import func
import enum

from .database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    username = Column(String(64), unique=True, nullable=False, comment="登录用户名，唯一")
    email = Column(String(128), unique=True, nullable=False, comment="邮箱，唯一")
    password_hash = Column(String(255), nullable=False, comment="bcrypt加密后的密码")
    full_name = Column(String(128), nullable=True, comment="用户全名（可选）")
    role = Column(
        Enum(UserRole, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=UserRole.USER,
        comment="角色：admin=管理员, user=普通用户",
    )
    is_active = Column(SmallInteger, nullable=False, default=1, comment="是否启用：1=启用，0=禁用")
    avatar_url = Column(String(512), nullable=True, comment="头像URL（可选）")
    last_login_at = Column(DateTime, nullable=True, comment="最后登录时间")
    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=True, onupdate=func.now(), comment="更新时间")


class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="知识库ID")
    name = Column(String(255), nullable=False, comment="知识库名称")
    description = Column(Text, nullable=True, comment="描述")
    document_count = Column(Integer, nullable=False, default=0, comment="文档数量")
    creator_username = Column(String(50), nullable=False, comment="创建者用户名")
    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=True, onupdate=func.now(), comment="最后更新时间")
    is_deleted = Column(SmallInteger, nullable=False, default=0, comment="软删除标志，0-未删除，1-已删除")


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_document"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="文档ID")
    knowledge_base_id = Column(
        Integer,
        ForeignKey("knowledge_base.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属知识库ID",
    )
    file_name = Column(String(255), nullable=False, comment="文件名（含扩展名）")
    file_type = Column(String(50), nullable=False, comment="文件类型/扩展名")
    file_size_kb = Column(DECIMAL(10, 2), nullable=False, comment="文件大小（KB）")
    chunk_count = Column(Integer, nullable=False, default=0, comment="分块数")
    status = Column(String(20), nullable=False, default="pending", comment="状态：pending/ready/failed")
    uploaded_by = Column(String(50), nullable=True, comment="上传者用户名")
    uploaded_at = Column(DateTime, nullable=False, server_default=func.now(), comment="上传时间")
    file_path = Column(String(500), nullable=True, comment="文件存储路径")
    file_hash = Column(String(64), nullable=True, comment="文件哈希值（用于去重校验）")
    updated_at = Column(DateTime, nullable=True, onupdate=func.now(), comment="最后更新时间")
    is_deleted = Column(SmallInteger, nullable=False, default=0, comment="软删除标志，0-未删除，1-已删除")

    __table_args__ = (
        Index("idx_kb_id", "knowledge_base_id"),
    )


class ConversationHistory(Base):
    __tablename__ = "conversation_history"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    question = Column(String(500), nullable=False, comment="用户提出的问题")
    answer = Column(Text, nullable=False, comment="系统给出的回答")
    knowledge_base = Column(String(100), nullable=False, comment="引用的知识库名称")
    questioner = Column(String(50), nullable=False, comment="提问者姓名")
    create_time = Column(DateTime, nullable=False, server_default=func.now(), comment="提问时间")
    operation = Column(String(50), nullable=True, comment="操作按钮文本")
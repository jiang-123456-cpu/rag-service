import datetime
import logging
from typing import List, Optional

import jwt
from langchain_core.tools import tool

from services.rag_service import RagService
from services.recorder_service import reorder_service
from utils.auth import SECRET_KEY, ALGORITHM

logger = logging.getLogger(__name__)


@tool(
    description=(
        "用于从向量数据库里检索文档并生成摘要。"
        "需要提供查询问题 query 和知识库 ID kb_id（整数）。"
        "返回包含摘要和检索到的文档列表。"
        "注意：文档已经过自动重排序，无需再调用重排序工具"
    )
)
async def rag_summary_tools(query: str, kb_id: int) -> str:
    """RAG 摘要工具：基于知识库检索文档并生成回答摘要"""
    try:
        answer, source_docs = await RagService().ask(query, kb_id)
    except Exception as e:
        logger.exception("rag_summary_tools 执行失败")
        return f"RAG 检索失败: {e}"

    formatted_result = f"摘要: {answer}\n\n检索到的文档列表（已重排序）:\n"
    for i, doc in enumerate(source_docs, 1):
        file_path = doc.get("file_path", "未知来源")
        content = doc.get("content", "")
        formatted_result += f"{i}. [{file_path}] {content}\n"
    return formatted_result


@tool(
    description=(
        "用于对文档列表进行重排序，传入查询语句 query 和文档列表 documents（字符串列表），"
        "返回重排序后的文档列表，包含文档内容和相似度。"
        "注意：rag_summary_tools 已内置重排序功能，通常不需要单独调用此工具"
    )
)
async def reorder_documents_tools(query: str, documents: List[str]) -> str:
    """重排序文档工具"""
    result = await reorder_service.reorder_documents(query, documents)
    if not result.get("success"):
        return f"重排序失败: {result.get('message', '未知错误')}"

    ranked = result.get("documents", [])
    if not ranked:
        return "重排序完成，但未返回任何文档"

    formatted_result = "重排序后的文档列表:\n"
    for i, item in enumerate(ranked, 1):
        doc = item.get("document", "")
        # 兼容 document 为 {"text": "..."} 字典的情况
        if isinstance(doc, dict):
            doc = doc.get("text", doc.get("content", ""))
        similarity = item.get("similarity", 0.0)
        formatted_result += f"{i}. [相似度: {similarity:.4f}] {doc}\n"
    logger.info("重排序完成，共 %d 篇文档", len(ranked))
    return formatted_result


@tool(
    description=(
        "当用户明确询问自己的用户ID时，从 JWT token 中解析当前用户ID。"
        "参数为完整的 JWT token 字符串（可含或不含 'Bearer ' 前缀）。"
        "注意：当前项目的 token 中只包含用户ID，不包含用户名"
    )
)
async def get_user_info_tools(token: str) -> str:
    """获取用户信息工具：从 JWT 中解析用户ID"""
    token = (token or "").replace("Bearer ", "").replace("bearer ", "").strip()
    if not token:
        return "未提供有效的 token，无法获取用户信息"
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        return "token 已过期，请重新登录"
    except jwt.InvalidTokenError:
        return "无法解析 token，无法获取用户信息"

    user_id = payload.get("id", "未知")
    return f"用户信息：\n- 用户ID: {user_id}"


@tool(
    description=(
        "用于获取天气信息（演示用占位工具，未接入真实天气服务）。"
        "需要提供城市名称 city。注意：当前仅返回演示提示，不代表真实天气"
    )
)
async def get_weather_tools(city: Optional[str] = None) -> str:
    """获取天气工具（占位）"""
    if not city:
        return "请提供城市名称"
    return f"【{city}】（演示工具，未接入真实天气服务）"


@tool(description="用于获取当前年月日时分")
async def what_time_is_now() -> str:
    """获取当前年月日时分的工具"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"当前时间是：{now}"

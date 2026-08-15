"""
生产 Agent 工厂类
支持：
- 每次调用创建全新的 AgentExecutor 实例
- 动态注入工具、提示词、模型配置
- 支持异步流式调用
"""
import os
from typing import Any, List, Optional, Dict, AsyncIterator
from dataclasses import dataclass
import uuid

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_core.messages import AIMessageChunk, BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()


@dataclass
class AgentConfig:
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: str = "qwen3.7-max"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    streaming: bool = True
    timeout: Optional[int] = 60


class AgentFactory:
    def __init__(
        self,
        default_config: Optional[AgentConfig] = None,
        default_tools: Optional[List[BaseTool]] = None,
        default_system_prompt: Optional[str] = None,
    ):
        self._default_config = default_config or AgentConfig(
            api_key=os.getenv("api_key"),
            base_url=os.getenv("base_url"),
        )
        self._default_tools = default_tools or []
        self._default_system_prompt = default_system_prompt or (
            "你是一个专业的AI助手，基于提供的上下文和工具还有已经上传处理的文档信息来回答用户问题。"
            "如果问题无法通过现有信息解答，请诚实告知用户。"
        )
        self._memory = MemorySaver()

    def _build_chat_model(self, config: AgentConfig) -> BaseChatModel:
        if not config.api_key:
            raise ValueError("api_key 未配置，请检查 .env 文件")
        if not config.base_url:
            raise ValueError("base_url 未配置，请检查 .env 文件")

        return ChatOpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            model=config.model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            streaming=config.streaming,
            timeout=config.timeout,
        )

    def create_agent(
        self,
        tools: Optional[List[BaseTool]] = None,
        system_prompt: Optional[str] = None,
        model_config: Optional[Dict[str, Any]] = None,
        thread_id: Optional[str] = None,
    ):
        config_dict = self._default_config.__dict__.copy()
        if model_config:
            config_dict.update(model_config)
        config = AgentConfig(**config_dict)
        chat_model = self._build_chat_model(config)
        sys_prompt = system_prompt or self._default_system_prompt
        agent_tools = tools or self._default_tools

        # Ensure checkpointer (MemorySaver) always receives a thread_id to avoid errors.
        # NOTE: langgraph's astream/ainvoke takes `config` (RunnableConfig), and
        # `configurable` MUST live inside that dict. Passing it as a top-level
        # kwarg is silently ignored and makes the checkpointer raise
        # "Checkpointer requires one or more of the following 'configurable' keys: ...".
        if not thread_id:
            thread_id = f"thread-{uuid.uuid4().hex}"
        runnable_config: Dict[str, Any] = {"configurable": {"thread_id": thread_id}}

        agent = create_agent(
            model=chat_model,
            tools=agent_tools,
            system_prompt=sys_prompt,
            checkpointer=self._memory,
        )

        return agent, runnable_config

    async def ainvoke(
        self,
        messages: List[BaseMessage],
        tools: Optional[List[BaseTool]] = None,
        system_prompt: Optional[str] = None,
        model_config: Optional[Dict[str, Any]] = None,
        thread_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        agent, runnable_config = self.create_agent(
            tools=tools,
            system_prompt=system_prompt,
            model_config=model_config,
            thread_id=thread_id,
        )
        result = await agent.ainvoke({"messages": messages}, config=runnable_config)
        return result

    async def astream_content(
        self,
        messages: List[BaseMessage],
        tools: Optional[List[BaseTool]] = None,
        system_prompt: Optional[str] = None,
        model_config: Optional[Dict[str, Any]] = None,
        thread_id: Optional[str] = None,
    ) -> AsyncIterator[str]:
        agent, runnable_config = self.create_agent(
            tools=tools,
            system_prompt=system_prompt,
            model_config=model_config,
            thread_id=thread_id,
        )
        async for event in agent.astream(
            {"messages": messages},
            config=runnable_config,
            stream_mode="messages",
        ):
            # stream_mode="messages" yields 2-tuples: (LLM token / message, metadata).
            # Previously this used event[1] which is always the metadata dict, so the
            # generator never yielded any content and the UI showed "暂无回答".
            if isinstance(event, tuple) and len(event) >= 2:
                msg = event[0]
                if isinstance(msg, AIMessageChunk):
                    content = msg.content
                    if isinstance(content, str) and content:
                        yield content


_agent_factory_instance: Optional[AgentFactory] = None


def get_agent_factory() -> AgentFactory:
    global _agent_factory_instance
    if _agent_factory_instance is None:
        _agent_factory_instance = AgentFactory()
    return _agent_factory_instance

# RAG-Backend

基于 FastAPI 的检索增强生成（RAG）后端系统，支持知识库管理、文档向量化、智能问答和 Agent 智能体。

## 技术栈

- **FastAPI** - 现代 Web 框架
- **SQLAlchemy** - 异步 ORM
- **ChromaDB** - 向量数据库
- **LangChain / LangGraph** - LLM 应用框架
- **JWT** - 用户认证
- **Pydantic** - 数据验证
- **SQLite** - 关系型数据库

## 功能特性

- 用户注册 / 登录 / JWT 认证
- 知识库 CRUD 管理
- 文档上传（支持 TXT、MD、DOCX、PDF 等格式）
- 文档自动分块与向量化存储
- 基于 RAG 的智能问答（流式响应）
- 多轮对话历史记录
- Agent 智能体（工具调用）
- 数据可视化统计

## 项目结构

```
fastapi-learning/
├── agent/                      # Agent 智能体
│   ├── agent.py                # Agent 工厂
│   ├── agent_tools.py          # 自定义工具
│   └── agent_middleware.py     # Agent 中间件
├── config/                     # 配置文件
│   ├── chroma.yml              # ChromaDB 配置
│   ├── prompts.yml             # 提示词配置
│   └── rag.yml                 # RAG 配置
├── db/                         # 数据库
│   ├── database.py             # 数据库连接与会话管理
│   └── models.py               # SQLAlchemy 数据模型
├── model/                      # 模型层
│   └── factory.py              # LLM 模型工厂
├── prompts/                    # 提示词模板
│   ├── main_prompt.txt         # 主系统提示词
│   ├── rag_summarize.txt       # RAG 摘要提示词
│   └── report_prompt.txt       # 报告生成提示词
├── routers/                    # API 路由
│   ├── chat.py                 # 聊天对话接口
│   ├── document.py             # 文档管理接口
│   ├── KnowledgeBase.py        # 知识库管理接口
│   ├── users.py                # 用户管理接口
│   └── visualize.py            # 可视化统计接口
├── schemas/                    # Pydantic 数据模型
│   ├── chat.py                 # 聊天请求/响应模型
│   ├── document.py             # 文档请求/响应模型
│   ├── KnowledgeBase.py        # 知识库请求/响应模型
│   └── user.py                 # 用户请求/响应模型
├── services/                   # 业务服务层
│   ├── rag_service.py          # RAG 检索服务
│   ├── recorder_service.py     # 重排序服务
│   └── vector_service.py       # 向量服务
├── utils/                      # 工具函数
│   ├── auth.py                 # JWT 认证工具
│   ├── config_handler.py       # 配置读取
│   ├── file_handler.py         # 文件处理
│   ├── path_tool.py            # 路径工具
│   └── prompt_loader.py        # 提示词加载
├── uploads/                    # 上传文件存储目录
├── chroma_db/                  # ChromaDB 向量数据存储
├── scripts/                    # 脚本工具
├── main.py                     # 应用入口
├── requirements.txt            # Python 依赖
└── .env                        # 环境变量配置
```

## 快速开始

### 环境要求

- Python 3.11+
- 虚拟环境（推荐）

### 安装依赖

```bash
cd fastapi-learning
pip install -r requirements.txt
```

### 配置环境变量

复制 .env 文件并填入所需配置：

```
# 数据库连接
DATABASE_URL=sqlite+aiosqlite:///./rag.db

# JWT 密钥
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# LLM API 配置
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```

### 启动服务

```bash
# 开发模式（带热重载）
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

访问 API 文档：http://localhost:8000/docs

## API 接口

### 用户接口 /api/users

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/users/register | 用户注册 |
| POST | /api/users/login | 用户登录 |
| GET | /api/users/ | 获取用户列表 |
| POST | /api/users/disabled | 禁用用户（管理员） |
| POST | /api/users/unban | 解封用户（管理员） |
| POST | /api/users/verify | 验证用户状态 |
| POST | /api/users/change-password | 修改密码 |

### 知识库接口 /api/knowledgebase

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/knowledgebase/create | 创建知识库 |
| POST | /api/knowledgebase/update | 更新知识库 |
| POST | /api/knowledgebase/delete | 删除知识库 |
| GET | /api/knowledgebase/ | 分页查询知识库列表 |

### 文档接口 /api/document

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/document/list | 分页查询文档列表 |
| POST | /api/document/upload | 上传文档到知识库 |
| POST | /api/document/delete | 删除文档 |

### 聊天接口 /api/chat

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/chat/ask | 发送问题（流式响应） |
| GET | /api/chat/list | 获取会话历史列表 |

### 可视化接口 /api/visualize

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/visualize/amount | 获取数据统计概览 |

## 数据库模型

- **users** - 用户表（用户名、邮箱、密码、角色、状态）
- **knowledge_base** - 知识库表（名称、描述、创建者）
- **knowledge_document** - 文档表（文件名、类型、大小、分块数、关联知识库）
- **conversation_history** - 会话历史表（问题、回答、用户、知识库关联）

## 核心流程

### RAG 问答流程

1. 用户发送问题到 /api/chat/ask
2. 系统根据 kb_id 从 ChromaDB 检索相关文档片段
3. 使用重排序服务对检索结果进行排序
4. 将检索上下文 + 用户问题组装成提示词
5. 调用 LLM 生成回答（支持流式输出）
6. 保存会话历史到数据库

### 文档处理流程

1. 用户上传文档到 /api/document/upload
2. 解析文档内容并分块
3. 对每个分块进行向量化（Embedding）
4. 将向量存储到 ChromaDB（关联 kb_id）
5. 记录文档元数据到数据库

## 配置说明

### config/chroma.yml

ChromaDB 向量数据库配置（集合名称、持久化路径等）。

### config/rag.yml

RAG 检索配置（Top-K、相似度阈值等）。

### config/prompts.yml

提示词模板路径配置。

## 许可证

MIT License

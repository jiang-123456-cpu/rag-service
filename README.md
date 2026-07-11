# RAG-Backend

这是一个 Retrieval-Augmented Generation (RAG) 项目后端，用于：
- 将用户上传或现有文档切分、向量化并存入本地向量数据库（Chroma）。
- 使用检索到的片段与 LLM（配置化）联合生成对话、摘要或报告。

主要技术栈：FastAPI、LangChain（core/社区加载器）、Chroma、本地/远程大模型（通过配置指定）。

特性
- 文档加载（txt/pdf/md/docx）与 MD5 去重
- 向量化并持久化到 Chroma（config/chroma.yml）
- 可配置的系统/摘要/报告 prompts（prompts/）
- 支持文件上传（uploads/）与 API 路由（routers/）

快速开始（Windows）
1. 克隆仓库并进入目录：
   cd path\to\repo
2. 创建并激活虚拟环境：
   python -m venv .venv
   .venv\Scripts\activate
3. 安装依赖（若项目无 requirements.txt，请安装下面列出的包）：
   pip install fastapi uvicorn pyyaml chromadb langchain-core langchain-community python-docx
4. 启动开发服务器：
   uvicorn main:app --reload --host 127.0.0.1 --port 8000
5. API 文档：
   - Swagger: http://127.0.0.1:8000/docs
   - ReDoc:  http://127.0.0.1:8000/redoc

主要配置文件
- config/rag.yml：RAG 相关模型名称（示例：chat_model_name、embedding_model_name）
- config/chroma.yml：Chroma 设置（collection_name、persist_directory、chunk_size、md5 存储等）
- config/prompts.yml：prompts 文件路径（prompts/main_prompt.txt 等）

关键目录说明
- main.py                 # FastAPI 应用入口，包含路由挂载（users, KnowledgeBase, document, chat）
- routers/                # API 路由集合（users、KnowledgeBase、document、chat）
- utils/                  # 工具模块：file_handler（加载/切分/MD5）、config_handler、prompt_loader、path_tool
- prompts/                # 文本型 prompts（main_prompt.txt / rag_summarize.txt / report_prompt.txt）
- config/                 # YAML 配置文件
- uploads/                # 上传文件临时存放
- chroma_db/              # （默认）Chroma 持久化目录（由 config/chroma.yml 指定）
- md5.txt                 # 已处理文件的 md5 列表（去重用）

运行说明与注意事项
- 修改模型或 embedding 名称请更新 config/rag.yml
- 若使用本地重排序/检索模型，保证路径（如 config 中的 RERANKER_MODEL_PATH）可被访问
- 文件上传后，服务会计算 md5 并检查 md5.txt 来避免重复索引
- prompts 通过 utils/prompt_loader.py 读取，请确保 prompts.yml 的路径正确

开发与调试
- 遇到依赖/导入问题，先确认虚拟环境已激活且依赖已安装
- utils 中的 get_abs_path() 基于项目根目录构建路径，注意在脚本或测试中使用相对路径时保持一致

部署建议
- 生产环境使用 Gunicorn + Uvicorn worker 或其它 ASGI 进程管理方案
- 将 Chroma 数据目录映射到持久存储（容器部署时请使用卷）
- 使用环境变量管理凭证与模型路径，避免将密钥写入仓库

贡献
欢迎 PR / Issue。提交变更前请尽量包含可复现步骤与相关配置说明。

许可证
按项目需要选择合适许可证（例如 MIT）。

如果需要，将 README 翻译为英文、补充示例请求/响应或把具体启动命令改为生产环境脚本。# rag-service

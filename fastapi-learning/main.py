from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import users,KnowledgeBase,document,chat

app = FastAPI()
# 配置 CORS
origins = [
    "http://localhost:3000",      # 前端开发服务器地址
    "http://127.0.0.1:3000",
    # 如果需要其他来源，可以继续添加，或者使用 "*" 允许所有（不推荐生产环境）
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,                # 允许的源
    allow_credentials=True,               # 允许携带 cookie
    allow_methods=["*"],                  # 允许所有 HTTP 方法（GET, POST, PUT, DELETE 等）
    allow_headers=["*"],                  # 允许所有请求头
)

@app.get("/")
async def read_root():
   return {"Hello": "World"}
# @app.get("/items/{item_id}")
# def read_item(item_id: int, q: str = None):
#    return {"item_id": item_id, "q": q}

app.include_router(users.router)
app.include_router(KnowledgeBase.router)
app.include_router(document.router)
app.include_router(chat.router)


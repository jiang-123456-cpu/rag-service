from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
import bcrypt
import datetime

from routers import users, KnowledgeBase, document, chat, visualize
from db.database import AsyncSessionLocal, engine
from db.models import Users, UserRole
from sqlalchemy import select


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Users).where(Users.username == "jay1234"))
            admin = result.scalar_one_or_none()
            if not admin:
                hashed_password = await asyncio.to_thread(
                    lambda: bcrypt.hashpw("jay1234".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                )
                admin = Users(
                    username="jay1234",
                    email="10000000000@qq.com",
                    password_hash=hashed_password,
                    role=UserRole.ADMIN,
                    is_active=1,
                    created_at=datetime.datetime.now(),
                )
                db.add(admin)
                await db.commit()
        except Exception:
            await db.rollback()
    yield


app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"服务器内部错误: {str(exc)}"},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.get("/")
async def read_root():
   return {"Hello": "World"}

app.include_router(users.router)
app.include_router(KnowledgeBase.router)
app.include_router(document.router)
app.include_router(chat.router)
app.include_router(visualize.router)

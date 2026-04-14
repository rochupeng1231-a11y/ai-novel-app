"""
AI 写小说应用 - FastAPI 主入口
"""
import os
from dotenv import load_dotenv

# 加载 .env 环境变量
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import chapters, characters, writing
from backend.api.batch_writing import router as batch_router
from backend.api.database import router as database_router
from backend.api.rollback import router as rollback_router
from backend.api.continuity import router as continuity_router

app = FastAPI(title="AI 写小说 API", version="0.2.0")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chapters.router, prefix="/api/chapters", tags=["章节"])
app.include_router(characters.router, prefix="/api/characters", tags=["角色"])
app.include_router(writing.router, prefix="/api/writing", tags=["写作"])
app.include_router(batch_router, prefix="/api/writing", tags=["批量写作"])
app.include_router(database_router, tags=["数据库"])
app.include_router(rollback_router, tags=["多维度回退"])
app.include_router(continuity_router, prefix="/api/continuity", tags=["章节连贯性"])


@app.get("/")
def root():
    return {"message": "AI 写小说 API", "version": "0.2.0"}


@app.get("/health")
def health():
    return {"status": "ok"}

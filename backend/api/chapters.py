"""
章节 API
"""
from fastapi import APIRouter, HTTPException
from typing import List
from backend.models.schemas import (
    ChapterCreate,
    ChapterUpdate,
    ChapterResponse
)

router = APIRouter()

# 模拟数据存储（后续替换为数据库）
CHAPTERS_DB = {}


@router.post("/", response_model=ChapterResponse)
async def create_chapter(chapter: ChapterCreate):
    """创建章节"""
    # TODO: 接入数据库
    return {
        "id": "temp-id",
        "project_id": chapter.project_id,
        "number": chapter.number,
        "title": chapter.title,
        "content": "",
        "status": "draft",
        "word_count": 0,
        "tension_score": 0.5,
        "created_at": "2026-04-12T00:00:00",
        "updated_at": "2026-04-12T00:00:00"
    }


@router.get("/project/{project_id}", response_model=List[ChapterResponse])
async def get_chapters(project_id: str):
    """获取项目的所有章节"""
    # TODO: 接入数据库
    return []


@router.get("/{chapter_id}", response_model=ChapterResponse)
async def get_chapter(chapter_id: str):
    """获取单个章节"""
    # TODO: 接入数据库
    raise HTTPException(status_code=404, detail="Chapter not found")


@router.put("/{chapter_id}", response_model=ChapterResponse)
async def update_chapter(chapter_id: str, chapter: ChapterUpdate):
    """更新章节"""
    # TODO: 接入数据库
    raise HTTPException(status_code=404, detail="Chapter not found")


@router.delete("/{chapter_id}")
async def delete_chapter(chapter_id: str):
    """删除章节"""
    # TODO: 接入数据库
    return {"message": "Deleted"}

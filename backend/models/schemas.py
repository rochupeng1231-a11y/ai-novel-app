"""
Pydantic 数据模型
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ChapterBase(BaseModel):
    number: int
    title: Optional[str] = None


class ChapterCreate(ChapterBase):
    project_id: str


class ChapterUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None


class ChapterResponse(ChapterBase):
    id: str
    project_id: str
    content: Optional[str] = None
    status: str
    word_count: int
    tension_score: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CharacterBase(BaseModel):
    name: str
    alias: Optional[str] = None
    personality: Optional[str] = None
    speech_style: Optional[str] = None


class CharacterCreate(CharacterBase):
    project_id: str
    forbidden_topics: Optional[List[str]] = []


class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    alias: Optional[str] = None
    personality: Optional[str] = None
    speech_style: Optional[str] = None
    forbidden_topics: Optional[List[str]] = None


class CharacterResponse(CharacterBase):
    id: str
    project_id: str
    forbidden_topics: List[str]
    avatar_url: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class WritingRequest(BaseModel):
    chapter_id: str
    instruction: str  # 续写/润色/改写/概括
    context: Optional[str] = None  # 额外上下文


class WritingResponse(BaseModel):
    content: str
    tension_score: float
    tokens_used: int


class BatchWritingRequest(BaseModel):
    """批量写作请求"""
    project_id: str
    chapter_ids: list[str]  # 要写的章节ID列表（按顺序）
    instruction: str = "续写"


class BatchWritingStatus(BaseModel):
    """批量写作状态"""
    batch_id: str
    total_chapters: int
    current_index: int
    current_chapter_id: str
    status: str  # pending/writing/waiting_review/completed
    current_content: str = ""

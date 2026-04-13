"""
角色 API
"""
from fastapi import APIRouter, HTTPException
from typing import List
from backend.models.schemas import (
    CharacterCreate,
    CharacterUpdate,
    CharacterResponse
)

router = APIRouter()


@router.post("/", response_model=CharacterResponse)
async def create_character(character: CharacterCreate):
    """创建角色"""
    # TODO: 接入数据库
    return {
        "id": "temp-id",
        "project_id": character.project_id,
        "name": character.name,
        "alias": character.alias,
        "personality": character.personality,
        "speech_style": character.speech_style,
        "forbidden_topics": character.forbidden_topics or [],
        "avatar_url": None,
        "created_at": "2026-04-12T00:00:00"
    }


@router.get("/project/{project_id}", response_model=List[CharacterResponse])
async def get_characters(project_id: str):
    """获取项目的所有角色"""
    # TODO: 接入数据库
    return []


@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(character_id: str):
    """获取单个角色"""
    # TODO: 接入数据库
    raise HTTPException(status_code=404, detail="Character not found")


@router.put("/{character_id}", response_model=CharacterResponse)
async def update_character(character_id: str, character: CharacterUpdate):
    """更新角色"""
    # TODO: 接入数据库
    raise HTTPException(status_code=404, detail="Character not found")


@router.delete("/{character_id}")
async def delete_character(character_id: str):
    """删除角色"""
    # TODO: 接入数据库
    return {"message": "Deleted"}

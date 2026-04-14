# -*- coding: utf-8 -*-
"""
Continuity API - 后端任务处理

提供章节写完后的分析接口
"""
import asyncio
import json
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database.models import get_db, Chapter, Project, Character
from backend.services.continuity import (
    ContinuityEngine,
    TimelineGraph,
    StateTracker,
    TropeTracker,
    ForeshadowManager,
    FactExtractor,
    ConsistencyChecker
)

router = APIRouter()


class ChapterAnalysisRequest(BaseModel):
    chapter_id: str
    chapter_content: str = None  # 可选，不提供则从数据库读取


class ChapterStateUpdate(BaseModel):
    character_id: str
    location: str = None
    emotion: str = None
    physical_state: str = None
    goal: str = None
    status: str = None


@router.post("/analyze")
async def analyze_chapter(
    request: ChapterAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    分析章节内容并更新状态

    提取：
    - 时间事件
    - 角色状态变化
    - 套路使用
    """
    chapter = db.query(Chapter).filter(Chapter.id == request.chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")

    content = request.chapter_content or chapter.content
    if not content:
        raise HTTPException(status_code=400, detail="章节内容为空")

    project = db.query(Project).filter(Project.id == chapter.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 创建引擎实例
    engine = ContinuityEngine(db)

    # 1. 提取并记录套路使用
    trope_tracker = TropeTracker(db)
    tropes = trope_tracker.extract_tropes_from_chapter(content)
    trope_tracker.record_trope_usage(project.id, chapter.id, tropes)

    # 2. 基础时间事件（简化版）
    timeline = TimelineGraph(db)

    # 提取关键动作和对话
    events = _extract_simple_events(content)
    for event_data in events:
        timeline.add_event(
            project_id=project.id,
            chapter_id=chapter.id,
            **event_data
        )

    # 3. 更新世界状态（简化版）
    state_tracker = StateTracker(db)
    if not state_tracker.get_world_state(project.id):
        state_tracker.init_world_state(project.id, chapter.id)

    # 4. 初始化角色状态（如果需要）
    state_tracker.init_character_states(project.id)

    # 5. 记录伏笔触发（如果有）
    foreshadow_manager = ForeshadowManager(db)
    _check_foreshadow_trigger(db, foreshadow_manager, project.id, chapter.id, content)

    return {
        "success": True,
        "chapter_id": chapter.id,
        "chapter_number": chapter.number,
        "extracted": {
            "events": len(events),
            "tropes": tropes,
        }
    }


@router.post("/state/update")
async def update_character_state(
    update: ChapterStateUpdate,
    chapter_id: str,
    db: Session = Depends(get_db)
):
    """
    更新角色状态

    前端可以调用此接口来更新角色状态
    """
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")

    state_tracker = StateTracker(db)

    update_data = {}
    if update.location:
        update_data["location"] = update.location
    if update.emotion:
        update_data["emotion"] = update.emotion
    if update.physical_state:
        update_data["physical_state"] = update.physical_state
    if update.goal:
        update_data["goal"] = update.goal
    if update.status:
        update_data["status"] = update.status

    if update_data:
        state_tracker.update_character_state(
            character_id=update.character_id,
            chapter_id=chapter_id,
            **update_data
        )

    return {"success": True, "updated": update_data}


@router.get("/summary/{project_id}")
async def get_project_summary(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    获取项目的连贯性摘要

    包含：时间线、角色状态、伏笔、矛盾等统计
    """
    engine = ContinuityEngine(db)
    summary = engine.get_project_summary(project_id)
    return summary


@router.get("/timeline/{project_id}")
async def get_project_timeline(
    project_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """获取项目时间线"""
    timeline = TimelineGraph(db)
    events = timeline.get_project_timeline(project_id, limit)

    return {
        "events": [
            {
                "id": e.id,
                "chapter_id": e.chapter_id,
                "event_type": e.event_type,
                "content": e.content,
                "importance": e.importance,
                "created_at": e.created_at.isoformat() if e.created_at else None
            }
            for e in events
        ]
    }


@router.get("/trope/warning/{project_id}")
async def get_trope_warning(
    project_id: str,
    chapter_number: int = 1,
    db: Session = Depends(get_db)
):
    """
    获取套路警告

    用于大纲/章节生成时提醒避免重复套路
    """
    trope_tracker = TropeTracker(db)
    warning = trope_tracker.format_trope_instruction(project_id, chapter_number)
    stats = trope_tracker.get_trope_statistics(project_id)

    return {
        "warning": warning,
        "statistics": stats,
        "has_warning": len(warning) > 0
    }


@router.post("/foreshadow/from_outline")
async def plant_foreshadow_from_outline(
    project_id: str,
    outline: str,
    first_chapter_id: str = None,
    db: Session = Depends(get_db)
):
    """
    从大纲中识别并埋设伏笔

    分析大纲文本，识别潜在的伏笔并创建三元组
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 获取第一章ID（如果未指定）
    if not first_chapter_id:
        first_chapter = db.query(Chapter).filter(
            Chapter.project_id == project_id
        ).order_by(Chapter.number).first()
        if first_chapter:
            first_chapter_id = first_chapter.id

    foreshadow_manager = ForeshadowManager(db)
    planted = foreshadow_manager.plant_foreshadow_from_outline(
        project_id=project_id,
        outline=outline,
        first_chapter_id=first_chapter_id
    )

    return {
        "success": True,
        "planted_count": len(planted),
        "foreshadows": planted
    }


@router.get("/check/{project_id}")
async def pre_write_check(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    写前一致性检查

    在开始写新章节前，检查是否有一致性问题
    返回警告列表，用户需确认后继续
    """
    checker = ConsistencyChecker(db)
    warnings = checker.pre_write_check(project_id)

    high_severity = [w for w in warnings if w.get("severity") == "high"]
    medium_severity = [w for w in warnings if w.get("severity") == "medium"]
    low_severity = [w for w in warnings if w.get("severity") == "low"]

    return {
        "has_high_severity": len(high_severity) > 0,
        "warnings": {
            "high": high_severity,
            "medium": medium_severity,
            "low": low_severity
        },
        "total": len(warnings),
        "report": checker.get_consistency_report(project_id)
    }


@router.get("/character_states/{project_id}")
async def get_character_states(
    project_id: str,
    db: Session = Depends(get_db)
):
    """获取角色状态列表"""
    state_tracker = StateTracker(db)
    states = state_tracker.get_project_character_states(project_id)

    result = []
    for s in states:
        char = db.query(Character).filter(Character.id == s.character_id).first()
        if char:
            result.append({
                "character_id": s.character_id,
                "character_name": char.name,
                "location": s.location,
                "emotion": s.emotion,
                "physical_state": s.physical_state,
                "goal": s.goal,
                "status": s.status,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None
            })

    return {"states": result}


# ============================================================
# 辅助函数
# ============================================================

def _extract_simple_events(content: str) -> list[dict]:
    """
    简单事件提取（基于规则的降级方案）

    实际产品应使用LLM分析
    """
    events = []

    # 提取包含引号的对话
    dialogues = []
    import re
    for match in re.finditer(r'[""\']([^""\']{5,100})[""\']', content):
        dialogues.append(match.group(1))

    if dialogues:
        events.append({
            "event_type": "dialogue",
            "content": f"对话{dialogues[0][:30]}..." if dialogues else "有对话",
            "importance": "normal",
            "characters_involved": []
        })

    # 提取动作关键词
    action_keywords = {
        "打": "action",
        "杀": "action",
        "攻击": "action",
        "拿出": "action",
        "获得": "action",
        "走到": "action",
        "笑着说": "emotion_change",
        "哭着": "emotion_change",
        "愤怒": "emotion_change",
        "惊讶": "emotion_change",
        "叹气": "emotion_change",
    }

    found_actions = []
    for keyword, event_type in action_keywords.items():
        if keyword in content:
            found_actions.append((keyword, event_type))

    if found_actions:
        # 去重
        seen = set()
        unique_actions = []
        for keyword, event_type in found_actions:
            if keyword not in seen:
                seen.add(keyword)
                unique_actions.append((keyword, event_type))

        for keyword, event_type in unique_actions[:3]:
            events.append({
                "event_type": event_type,
                "content": f"包含动作：{keyword}",
                "importance": "normal",
                "characters_involved": []
            })

    return events


def _check_foreshadow_trigger(
    db: Session,
    foreshadow_manager: ForeshadowManager,
    project_id: str,
    chapter_id: str,
    content: str
):
    """检查伏笔是否被触发"""
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        return

    planted = foreshadow_manager.get_planted_foreshadows(project_id, "planted")

    for fs in planted:
        if foreshadow_manager.check_foreshadow_in_content(fs.id, content):
            foreshadow_manager.trigger_foreshadow(fs.id, chapter_id)

# -*- coding: utf-8 -*-
"""
写作 API - 核心写作能力（单章节流式）
"""
import json
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.models.schemas import WritingRequest
from backend.services.writing_engine import WritingEngine
from backend.services.ai_client import stream_generate
from backend.services.continuity import ContinuityEngine
from backend.config import MAX_TOKENS
from database.models import get_db, Project, Chapter, Character

router = APIRouter()
writing_engine = WritingEngine()


def get_continuity_context(chapter_id: str, db: Session) -> dict:
    """使用ContinuityEngine获取增强的写作上下文"""
    try:
        chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if not chapter:
            return {"base_context": "", "chapter": None, "project": None}

        project = db.query(Project).filter(Project.id == chapter.project_id).first()
        if not project:
            return {"base_context": "", "chapter": chapter, "project": None}

        engine = ContinuityEngine(db)
        continuity_data = engine.prepare_writing_context(
            project_id=project.id,
            chapter_id=chapter_id,
            chapter_number=chapter.number
        )

        context_parts = []
        if project.novel_type:
            context_parts.append(f"【小说类型】{project.novel_type}")
        if project.core_elements:
            try:
                elements = json.loads(project.core_elements) if isinstance(project.core_elements, str) else project.core_elements
                if elements:
                    context_parts.append(f"【核心元素】{', '.join(elements)}")
            except:
                pass
        if project.outline:
            context_parts.append(f"【故事大纲】\n{project.outline}")

        characters = db.query(Character).filter(Character.project_id == project.id).all()
        if characters:
            char_info = "【主要角色】\n"
            for c in characters:
                char_info += f"- {c.name}"
                if c.alias:
                    char_info += f"（{c.alias}）"
                if c.personality:
                    char_info += f"，性格：{c.personality}"
                char_info += "\n"
            context_parts.append(char_info)

        return {
            "base_context": "\n\n".join(context_parts),
            "character_states": continuity_data.get("character_states", ""),
            "previous_context": continuity_data.get("previous_context", ""),
            "foreshadow_context": continuity_data.get("foreshadow_context", ""),
            "trope_warning": continuity_data.get("trope_warning", ""),
            "consistency_warnings": continuity_data.get("consistency_warnings", []),
            "recent_events": continuity_data.get("recent_events", []),
            "chapter": chapter,
            "project": project,
            "continuity_engine": engine
        }
    except Exception as e:
        print(f"获取Continuity上下文失败: {e}")
        return {"base_context": "", "chapter": None, "project": None}


@router.post("/")
async def write_stream(writing_request: WritingRequest, db: Session = Depends(get_db)):
    """流式写作任务，内容实时推送至前端"""
    async def event_stream():
        continuity_engine = None
        chapter_obj = None
        project_obj = None

        context = writing_request.context or ""
        if not context and writing_request.instruction == "续写":
            continuity = get_continuity_context(writing_request.chapter_id, db)
            chapter_obj = continuity.get("chapter")
            project_obj = continuity.get("project")
            continuity_engine = continuity.get("continuity_engine")
            project_context = continuity.get("base_context", "")
            prev_context = continuity.get("previous_context", "")

            print(f"[Continuity] 章号: {chapter_obj.number if chapter_obj else 'N/A'}, 上下文: {len(prev_context)}字")

            if project_context and chapter_obj:
                context_parts = [f"【当前章节】第{chapter_obj.number}章：{chapter_obj.title}"]
                if prev_context:
                    context_parts.append(f"\n【上一章情节承接】\n{prev_context}")
                char_states = continuity.get("character_states", "")
                if char_states:
                    context_parts.append(f"\n【角色当前状态】\n{char_states}")
                foreshadow = continuity.get("foreshadow_context", "")
                if foreshadow:
                    context_parts.append(f"\n{foreshadow}")
                trope_warning = continuity.get("trope_warning", "")
                if trope_warning:
                    context_parts.append(f"\n{trope_warning}")
                warnings = continuity.get("consistency_warnings", [])
                if warnings:
                    high = [w for w in warnings if w.get("severity") == "high"]
                    if high:
                        context_parts.append("\n【一致性警告】")
                        for w in high:
                            context_parts.append(f"  ⚠ {w.get('message', '')}")
                context_parts.append(f"\n【项目背景】\n{project_context}")
                context_parts.append("\n【写作要求】请承接上文，延续角色状态，推进情节发展。")
                context = "\n".join(context_parts)
            elif project_context:
                context = f"【项目背景】\n{project_context}\n\n【已有内容】\n（暂无，请根据以上项目背景开始创作新章节）"
            else:
                context = "（暂无已有内容，请直接开始创作）"

        prompt = writing_engine._build_prompt(writing_request.instruction, context)
        extra_params = {"max_tokens": MAX_TOKENS}

        try:
            full_content = []
            async for chunk in stream_generate(prompt, **extra_params):
                full_content.append(chunk)
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"

            final_content = "".join(full_content)
            tension_score = writing_engine.tension_analyzer.analyze(final_content)["overall"]
            yield f"data: {json.dumps({'type': 'done', 'content': final_content, 'tension_score': tension_score, 'tokens_used': len(final_content) // 4}, ensure_ascii=False)}\n\n"

            if continuity_engine and chapter_obj and project_obj:
                print(f"[Continuity] 章节完成: {chapter_obj.title}")

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/stop/{task_id}")
async def stop_write(task_id: str):
    """停止正在进行的写作任务"""
    success = writing_engine.stop_task(task_id)
    return {"message": "任务已停止" if success else "任务不存在或已结束", "task_id": task_id}


@router.get("/status/{task_id}")
async def get_write_status(task_id: str):
    """获取写作任务状态"""
    status = writing_engine.get_task_status(task_id)
    if status:
        return status
    raise HTTPException(status_code=404, detail="任务不存在")


class TensionReviewRequest(BaseModel):
    content: str
    chapter_context: str = ""


class TensionIssue(BaseModel):
    dimension: str
    score: float
    level: str
    suggestion: str


@router.post("/tension/review")
async def tension_review(request: TensionReviewRequest):
    """张力审核 - 详细分析文本张力并提供改进建议"""
    return writing_engine.analyze_tension_detailed(
        content=request.content,
        chapter_context=request.chapter_context
    )

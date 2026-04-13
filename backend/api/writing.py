"""
写作 API - 核心写作能力
"""
import asyncio
import json
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.models.schemas import WritingRequest, WritingResponse
from backend.services.writing_engine import WritingEngine
from backend.services.ai_client import ai_aggregator
from backend.config import MAX_TOKENS
from database.models import get_db, Project, Chapter, Character

router = APIRouter()
writing_engine = WritingEngine()


async def get_project_context(chapter_id: str, db: Session) -> str:
    """当章节内容为空时，获取项目上下文（大纲+角色）"""
    try:
        chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if not chapter:
            return ""
        project = db.query(Project).filter(Project.id == chapter.project_id).first()
        if not project:
            return ""

        context_parts = []

        # 添加小说类型
        if project.novel_type:
            context_parts.append(f"【小说类型】{project.novel_type}")

        # 添加核心元素
        if project.core_elements:
            try:
                elements = json.loads(project.core_elements) if isinstance(project.core_elements, str) else project.core_elements
                if elements:
                    context_parts.append(f"【核心元素】{', '.join(elements)}")
            except:
                pass

        # 添加大纲
        if project.outline:
            context_parts.append(f"【故事大纲】\n{project.outline}")

        # 添加角色信息
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

        return "\n\n".join(context_parts)
    except Exception as e:
        print(f"获取项目上下文失败: {e}")
        return ""


@router.post("/")
async def write_stream(writing_request: WritingRequest, db: Session = Depends(get_db)):
    """
    流式写作任务，内容实时推送至前端
    """
    async def event_stream():
        task_type_map = {
            "大纲": "outline", "续写": "draft", "润色": "polish",
            "改写": "polish", "概括": "outline"
        }
        task_type = task_type_map.get(writing_request.instruction, "draft")

        # 当 context 为空且是续写时，自动获取项目上下文
        context = writing_request.context or ""
        if not context and writing_request.instruction == "续写":
            # 获取章节信息
            chapter = None
            if writing_request.chapter_id:
                chapter = db.query(Chapter).filter(Chapter.id == writing_request.chapter_id).first()

            project_context = await get_project_context(writing_request.chapter_id, db)
            if project_context and chapter:
                context = f"【当前章节】第{chapter.number}章：{chapter.title}\n\n【项目背景】\n{project_context}\n\n【已有内容】\n（暂无，请根据以上信息，撰写\"第{chapter.number}章：{chapter.title}\"的完整章节内容）"
            elif project_context:
                context = f"【项目背景】\n{project_context}\n\n【已有内容】\n（暂无，请根据以上项目背景开始创作新章节）"
            else:
                context = "（暂无已有内容，请直接开始创作）"

        prompt = writing_engine._build_prompt(writing_request.instruction, context)

        # 设置较大的 max_tokens，让 prompt 控制实际输出
        extra_params = {"max_tokens": MAX_TOKENS}

        print(f"[写作] 开始生成, instruction={writing_request.instruction}, extra_params={extra_params}")

        try:
            full_content = []
            chunk_count = 0
            async for chunk, model_name in ai_aggregator.stream_generate(task_type, prompt, **extra_params):
                full_content.append(chunk)
                chunk_count += 1
                # 实时推送每个字符块
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
            print(f"[写作] 完成，共 {chunk_count} 个 chunk，内容长度: {len(''.join(full_content))}")

            final_content = "".join(full_content)
            tension_score = writing_engine.tension_analyzer.analyze(final_content)["overall"]

            yield f"data: {json.dumps({'type': 'done', 'content': final_content, 'tension_score': tension_score, 'tokens_used': len(final_content) // 4}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/stop/{task_id}")
async def stop_write(task_id: str):
    """
    停止正在进行的写作任务
    """
    success = writing_engine.stop_task(task_id)
    if success:
        return {"message": "任务已停止", "task_id": task_id}
    else:
        return {"message": "任务不存在或已结束", "task_id": task_id}


@router.get("/status/{task_id}")
async def get_write_status(task_id: str):
    """
    获取写作任务状态
    """
    status = writing_engine.get_task_status(task_id)
    if status:
        return status
    else:
        raise HTTPException(status_code=404, detail="任务不存在")


class TensionReviewRequest(BaseModel):
    content: str
    chapter_context: str = ""  # 章节上下文


class TensionIssue(BaseModel):
    dimension: str  # 冲突/悬念/情感/节奏
    score: float
    level: str  # 高/中/低
    suggestion: str  # 改进建议


@router.post("/tension/review")
async def tension_review(request: TensionReviewRequest):
    """
    张力审核 - 详细分析文本张力并提供改进建议
    """
    result = writing_engine.analyze_tension_detailed(
        content=request.content,
        chapter_context=request.chapter_context
    )
    return result

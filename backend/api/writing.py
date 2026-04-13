"""
写作 API - 核心写作能力
"""
import asyncio
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.models.schemas import WritingRequest, WritingResponse
from backend.services.writing_engine import WritingEngine
from backend.services.ai_client import ai_aggregator

router = APIRouter()
writing_engine = WritingEngine()


@router.post("/")
async def write_stream(writing_request: WritingRequest):
    """
    流式写作任务，内容实时推送至前端
    """
    async def event_stream():
        task_type_map = {
            "大纲": "outline", "续写": "draft", "润色": "polish",
            "改写": "polish", "概括": "outline"
        }
        task_type = task_type_map.get(writing_request.instruction, "draft")
        prompt = writing_engine._build_prompt(writing_request.instruction, writing_request.context or "")

        try:
            full_content = []
            async for chunk, model_name in ai_aggregator.stream_generate(task_type, prompt):
                full_content.append(chunk)
                # 实时推送每个字符块
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"

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

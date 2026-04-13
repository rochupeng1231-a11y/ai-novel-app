"""
写作 API - 核心写作能力
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.models.schemas import WritingRequest, WritingResponse
from backend.services.writing_engine import WritingEngine

router = APIRouter()
writing_engine = WritingEngine()


@router.post("/", response_model=WritingResponse)
async def write(writing_request: WritingRequest):
    """
    执行写作任务
    
    instruction: 续写/润色/改写/概括
    """
    result = await writing_engine.execute(
        chapter_id=writing_request.chapter_id,
        instruction=writing_request.instruction,
        context=writing_request.context
    )
    return result


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

# -*- coding: utf-8 -*-
"""
批量写作 API - 仅做章节循环和审核状态管理
核心写作逻辑复用于单章节写作
"""
import uuid
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from backend.models.schemas import BatchWritingRequest
from database.models import get_db, Project, Chapter

router = APIRouter()

# 批量写作会话 (batch_id -> session)
_sessions = {}


def _get_session_or_404(batch_id: str, db: Session):
    """获取会话，不存在则抛404"""
    session = _sessions.get(batch_id)
    if not session:
        raise HTTPException(status_code=404, detail="批量写作会话不存在或已结束")
    return session


def _find_last_approved_chapter(session: dict) -> Chapter:
    """回溯找最近已批准内容的章节（确保上下文连贯）"""
    for i in range(session["current_index"] - 1, -1, -1):
        ch = session["chapters"][i]
        if ch.content and len(ch.content) > 0:
            return ch
    return None


@router.post("/batch/start")
async def batch_start(request: BatchWritingRequest, db: Session = Depends(get_db)):
    """启动批量写作，返回batch_id和第一章节信息"""
    project = db.query(Project).filter(Project.id == request.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    chapters = []
    for cid in request.chapter_ids:
        ch = db.query(Chapter).filter(Chapter.id == cid, Chapter.project_id == request.project_id).first()
        if not ch:
            raise HTTPException(status_code=404, detail=f"章节 {cid} 不存在")
        chapters.append(ch)

    batch_id = str(uuid.uuid4())
    _sessions[batch_id] = {
        "batch_id": batch_id,
        "project_id": request.project_id,
        "chapters": chapters,
        "current_index": 0,
        "instruction": request.instruction,
        "status": "pending"
    }

    ch = chapters[0]
    return {"batch_id": batch_id, "total_chapters": len(chapters),
            "current_chapter": {"id": ch.id, "number": ch.number, "title": ch.title}}


@router.get("/batch/{batch_id}/next-chapter")
async def batch_next_info(batch_id: str, db: Session = Depends(get_db)):
    """获取下一章节的信息（供前端调用单章写作API）"""
    session = _get_session_or_404(batch_id, db)

    if session["current_index"] >= len(session["chapters"]):
        return {"status": "completed", "message": "所有章节已完成"}

    ch = session["chapters"][session["current_index"]]
    last_approved = _find_last_approved_chapter(session)

    return {
        "status": "ready",
        "chapter_id": ch.id,
        "chapter_number": ch.number,
        "chapter_title": ch.title,
        "use_previous_content": last_approved.content[-500:] if last_approved else None,
        "use_previous_chapter_num": last_approved.number if last_approved else None
    }


@router.post("/batch/{batch_id}/complete-chapter")
async def batch_complete_chapter(
    batch_id: str,
    chapter_id: str,
    content: str,
    tension_score: float = 0.5,
    db: Session = Depends(get_db)
):
    """标记章节写作完成，进入待审核状态"""
    session = _get_session_or_404(batch_id, db)
    ch = session["chapters"][session["current_index"]]

    if ch.id != chapter_id:
        raise HTTPException(status_code=400, detail="章节ID不匹配")

    ch.status = "completed"
    ch.review_status = "pending"
    ch.tension_score = tension_score
    ch.word_count = len(content.replace(" ", "").replace("\n", ""))
    db.commit()

    session["status"] = "waiting_review"
    return {"status": "waiting_review", "chapter_id": chapter_id}


@router.post("/batch/{batch_id}/review")
async def batch_review(batch_id: str, action: str, content: str = None, db: Session = Depends(get_db)):
    """
    审核操作：approve/reject/skip/revise
    审核后自动进入下一章
    """
    session = _get_session_or_404(batch_id, db)
    ch = session["chapters"][session["current_index"]]

    if action == "approve":
        if content:
            ch.content = content
        ch.review_status = "approved"
        db.commit()
    elif action == "reject":
        ch.review_status = "rejected"
        db.commit()
    elif action == "skip":
        ch.review_status = "pending"
        ch.content = ""
        db.commit()
    elif action == "revise":
        if content:
            ch.content = content
        ch.review_status = "revised"
        db.commit()

    session["current_index"] += 1
    session["status"] = "pending"

    if session["current_index"] >= len(session["chapters"]):
        session["status"] = "completed"
        return {"status": "completed", "message": f"批量写作完成，共{len(session['chapters'])}章"}

    next_ch = session["chapters"][session["current_index"]]
    return {
        "status": "next",
        "current_index": session["current_index"],
        "total_chapters": len(session["chapters"]),
        "current_chapter": {"id": next_ch.id, "number": next_ch.number, "title": next_ch.title}
    }


@router.get("/batch/{batch_id}/status")
async def batch_status(batch_id: str):
    """获取批量写作状态"""
    session = _sessions.get(batch_id)
    if not session:
        raise HTTPException(status_code=404, detail="批量写作会话不存在")

    ch = session["chapters"][session["current_index"]] if session["current_index"] < len(session["chapters"]) else None
    return {
        "batch_id": batch_id,
        "status": session["status"],
        "current_index": session["current_index"],
        "total_chapters": len(session["chapters"]),
        "current_chapter": {"id": ch.id, "number": ch.number, "title": ch.title} if ch else None
    }

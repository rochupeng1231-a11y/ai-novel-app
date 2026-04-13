"""
多维度回退 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from database.models import get_db, Chapter, Character, CharacterRelation, Foreshadow
from backend.services.rollback_engine import RollbackEngine

router = APIRouter(prefix="/api/rollback", tags=["多维度回退"])


class RollbackRequest(BaseModel):
    target_type: str  # chapter, character, relation, foreshadow
    target_id: str
    version_number: Optional[int] = None


class ImpactPreview(BaseModel):
    chapters_to_rewrite: List[str]
    chapters_to_review: List[str]
    characters_affected: List[str]
    foreshadows_affected: List[str]
    total_impact: int


@router.get("/preview/{target_type}/{target_id}")
def preview_rollback(
    target_type: str,
    target_id: str,
    version_number: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    预览回退影响范围
    """
    engine = RollbackEngine(db)
    
    if version_number:
        preview = engine.preview_rollback(target_type, target_id, version_number)
    else:
        # 获取最新版本影响
        impact = engine.analyze_change_impact(target_type, target_id)
        preview = {
            "target": {"type": target_type, "id": target_id, "version": "latest"},
            "impact_summary": {
                "chapters_to_rewrite": len(impact.chapters_to_recheck),
                "chapters_to_review": len(impact.chapters_to_review),
                "characters_affected": len(impact.characters_affected),
                "foreshadows_affected": len(impact.foreshadows_affected),
                "total_impact": impact.total_changes
            },
            "affected_items": {
                "chapters_to_rewrite": impact.chapters_to_recheck,
                "chapters_to_review": impact.chapters_to_review,
                "characters": impact.characters_affected,
                "foreshadows": impact.foreshadows_affected
            }
        }
    
    return preview


@router.post("/execute")
def execute_rollback(
    request: RollbackRequest,
    db: Session = Depends(get_db)
):
    """
    执行多维度回退
    """
    engine = RollbackEngine(db)
    
    if request.target_type == "chapter" and not request.version_number:
        raise HTTPException(status_code=400, detail="章节回退需要指定版本号")
    
    result = engine.execute_rollback(
        request.target_type,
        request.target_id,
        request.version_number or 1
    )
    
    return result


@router.get("/history/{target_type}/{target_id}")
def get_change_history(
    target_type: str,
    target_id: str,
    db: Session = Depends(get_db)
):
    """
    获取变更历史
    """
    engine = RollbackEngine(db)
    history = engine.get_change_chain(target_type, target_id)
    return history


@router.get("/compare/{target_type}/{target_id}")
def compare_versions(
    target_type: str,
    target_id: str,
    version_a: int,
    version_b: int,
    db: Session = Depends(get_db)
):
    """
    比较两个版本的差异
    """
    from database.models import ChapterVersion
    
    if target_type != "chapter":
        raise HTTPException(status_code=400, detail="目前仅支持章节版本比较")
    
    v_a = db.query(ChapterVersion).filter(
        ChapterVersion.chapter_id == target_id,
        ChapterVersion.version_number == version_a
    ).first()
    
    v_b = db.query(ChapterVersion).filter(
        ChapterVersion.chapter_id == target_id,
        ChapterVersion.version_number == version_b
    ).first()
    
    if not v_a or not v_b:
        raise HTTPException(status_code=404, detail="版本不存在")
    
    # 简单统计差异
    content_a = v_a.content or ""
    content_b = v_b.content or ""
    
    words_a = len(content_a.replace(" ", ""))
    words_b = len(content_b.replace(" ", ""))
    
    return {
        "version_a": version_a,
        "version_b": version_b,
        "words_a": words_a,
        "words_b": words_b,
        "words_diff": words_b - words_a,
        "created_a": v_a.created_at.isoformat() if v_a.created_at else None,
        "created_b": v_b.created_at.isoformat() if v_b.created_at else None
    }

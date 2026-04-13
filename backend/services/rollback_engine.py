"""
多维度回退引擎
"""
import json
import re
from typing import List, Dict, Optional, Set
from datetime import datetime
from dataclasses import dataclass
from sqlalchemy.orm import Session


@dataclass
class Dependency:
    source_type: str
    source_id: str
    target_type: str
    target_id: str
    dependency_type: str  # references, triggers, contradicts


@dataclass
class RollbackImpact:
    """回退影响范围"""
    chapters_to_recheck: List[str]  # 需要重写的章节
    chapters_to_review: List[str]    # 需要检查的章节
    characters_affected: List[str]   # 受影响的角色
    foreshadows_affected: List[str]  # 受影响的伏笔
    total_changes: int


class RollbackEngine:
    """多维度回退引擎"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_change_impact(self, changed_type: str, changed_id: str) -> RollbackImpact:
        """
        分析变更的影响范围
        
        例如：修改角色A的关系，需要检查所有引用了该关系的章节
        """
        impact = RollbackImpact(
            chapters_to_recheck=[],
            chapters_to_review=[],
            characters_affected=[],
            foreshadows_affected=[],
            total_changes=0
        )
        
        # 根据变更类型查找相关依赖
        if changed_type == "character":
            # 角色变更：检查关系、伏笔、章节引用
            impact.characters_affected.append(changed_id)
            impact.chapters_to_review.extend(
                self._find_chapters_mentioning_character(changed_id)
            )
            
        elif changed_type == "relation":
            # 关系变更：检查涉及的章节
            rel = self._get_relation(changed_id)
            if rel:
                impact.characters_affected.extend([rel.character_a_id, rel.character_b_id])
                impact.chapters_to_review.extend(
                    self._find_chapters_mentioning_character(rel.character_a_id)
                )
                impact.chapters_to_review.extend(
                    self._find_chapters_mentioning_character(rel.character_b_id)
                )
                
        elif changed_type == "foreshadow":
            # 伏笔变更：检查相关章节
            fs = self._get_foreshadow(changed_id)
            if fs and fs.chapter_id:
                impact.foreshadows_affected.append(changed_id)
                # 伏笔状态变更可能影响后续章节
                impact.chapters_to_review.append(fs.chapter_id)
                
        elif changed_type == "chapter":
            # 章节变更：检查版本关联
            impact.chapters_to_recheck.append(changed_id)
        
        # 去重
        impact.chapters_to_recheck = list(set(impact.chapters_to_recheck))
        impact.chapters_to_review = list(set(impact.chapters_to_review))
        impact.characters_affected = list(set(impact.characters_affected))
        impact.foreshadows_affected = list(set(impact.foreshadows_affected))
        
        # 排除已在recheck的
        impact.chapters_to_review = [
            c for c in impact.chapters_to_review 
            if c not in impact.chapters_to_recheck
        ]
        
        impact.total_changes = (
            len(impact.chapters_to_recheck) +
            len(impact.chapters_to_review) +
            len(impact.characters_affected) +
            len(impact.foreshadows_affected)
        )
        
        return impact
    
    def execute_rollback(self, target_type: str, target_id: str, version_number: int) -> Dict:
        """
        执行多维度回退
        """
        # 1. 获取变更影响
        impact = self.analyze_change_impact(target_type, target_id)
        
        # 2. 执行实际的回退
        rollback_results = {}
        
        if target_type == "chapter":
            rollback_results["chapter"] = self._rollback_chapter(target_id, version_number)
        
        # 3. 标记受影响的章节需要重新检查
        rollback_results["impact"] = {
            "chapters_to_recheck": impact.chapters_to_recheck,
            "chapters_to_review": impact.chapters_to_review,
            "characters_affected": impact.characters_affected,
            "foreshadows_affected": impact.foreshadows_affected
        }
        
        return rollback_results
    
    def get_change_chain(self, target_type: str, target_id: str) -> List[Dict]:
        """
        获取变更链 - 追踪从当前版本到所有历史版本
        """
        chain = []
        
        if target_type == "chapter":
            from database.models import Chapter, ChapterVersion
            versions = self.db.query(ChapterVersion).filter(
                ChapterVersion.chapter_id == target_id
            ).order_by(ChapterVersion.version_number.desc()).all()
            
            for v in versions:
                chain.append({
                    "version_number": v.version_number,
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                    "change_summary": v.change_summary
                })
        
        return chain
    
    def preview_rollback(self, target_type: str, target_id: str, version_number: int) -> Dict:
        """
        预览回退效果
        """
        impact = self.analyze_change_impact(target_type, target_id)
        
        preview = {
            "target": {"type": target_type, "id": target_id, "version": version_number},
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
            },
            "recommendation": self._generate_recommendation(impact)
        }
        
        return preview
    
    def _find_chapters_mentioning_character(self, character_id: str) -> List[str]:
        """查找提及某角色的章节"""
        from database.models import Character, Chapter
        
        character = self.db.query(Character).filter(Character.id == character_id).first()
        if not character:
            return []
        
        # 在章节内容中搜索角色名
        chapters = self.db.query(Chapter).filter(
            Chapter.content.contains(character.name)
        ).all()
        
        return [c.id for c in chapters]
    
    def _get_relation(self, relation_id: str):
        from database.models import CharacterRelation
        return self.db.query(CharacterRelation).filter(
            CharacterRelation.id == relation_id
        ).first()
    
    def _get_foreshadow(self, foreshadow_id: str):
        from database.models import Foreshadow
        return self.db.query(Foreshadow).filter(
            Foreshadow.id == foreshadow_id
        ).first()
    
    def _rollback_chapter(self, chapter_id: str, version_number: int):
        from database.models import Chapter, ChapterVersion
        
        version = self.db.query(ChapterVersion).filter(
            ChapterVersion.chapter_id == chapter_id,
            ChapterVersion.version_number == version_number
        ).first()
        
        if not version:
            return {"success": False, "error": "版本不存在"}
        
        chapter = self.db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if chapter:
            chapter.content = version.content
            chapter.updated_at = datetime.utcnow()
            self.db.commit()
        
        return {"success": True, "restored_version": version_number}
    
    def _generate_recommendation(self, impact: RollbackImpact) -> str:
        """生成回退建议"""
        if impact.total_changes == 0:
            return "此次变更影响较小，可以安全回退。"
        elif impact.total_changes <= 3:
            return f"影响范围较小，建议回退后手动检查{len(impact.chapters_to_review)}个相关章节。"
        elif impact.total_changes <= 10:
            return f"影响范围中等，建议回退后批量检查{len(impact.chapters_to_review)}个章节的逻辑一致性。"
        else:
            return f"影响范围较大，建议先备份当前版本，再执行回退。"

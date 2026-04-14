# -*- coding: utf-8 -*-
"""
分类引导提取 + 矛盾配对 + 证据链服务

从章节中提取结构化事实，并检测矛盾
"""
import uuid
import hashlib
import json
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from database.models import ExtractedFact, Contradiction, Chapter, Character


class FactExtractor:
    """事实提取与矛盾检测器"""

    def __init__(self, db: Session):
        self.db = db

    # ============================================================
    # 事实提取
    # ============================================================

    def extract_facts_from_chapter(self, chapter_id: str) -> list[dict]:
        """
        从章节内容中提取结构化事实
        返回格式化的字典列表，实际由LLM填充

        返回结构:
        [
            {
                "category": "character_action",
                "subject": "林逸尘",
                "predicate": "获得了灵脉觉醒",
                "evidence_text": "林逸尘突然感到丹田一股热流...",
                "confidence": "high"
            },
            ...
        ]
        """
        chapter = self.db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if not chapter or not chapter.content:
            return []

        # 实际由LLM提取，这里返回空列表
        # 调用方需要使用LLM填充具体事实
        return []

    def add_fact(
        self,
        project_id: str,
        chapter_id: str,
        category: str,
        subject: str,
        predicate: str,
        evidence_text: str = None,
        evidence_chapter: str = None,
        confidence: str = "high"
    ) -> ExtractedFact:
        """添加提取的事实"""
        # 生成事实哈希
        fact_hash = self._generate_fact_hash(category, subject, predicate)

        fact = ExtractedFact(
            id=str(uuid.uuid4()),
            project_id=project_id,
            chapter_id=chapter_id,
            category=category,
            subject=subject,
            predicate=predicate,
            evidence_text=evidence_text,
            evidence_chapter=evidence_chapter or chapter_id,
            fact_hash=fact_hash,
            confidence=confidence,
            created_at=datetime.utcnow()
        )

        self.db.add(fact)
        self.db.commit()
        self.db.refresh(fact)

        # 检测新事实是否与已有事实矛盾
        self._check_contradiction(fact)

        return fact

    def _generate_fact_hash(self, category: str, subject: str, predicate: str) -> str:
        """生成事实哈希用于矛盾检测"""
        # 提取predicate的关键部分作为哈希依据
        # 例如: "情绪=愤怒" -> 取情绪作为键
        key_parts = []
        if "=" in predicate:
            key_parts.append(predicate.split("=")[0].strip())
        elif "是" in predicate:
            key_parts.append(predicate.split("是")[0].strip())
        elif "在" in predicate:
            key_parts.append(predicate.split("在")[0].strip())

        key = f"{category}:{subject}:{':'.join(key_parts)}"
        return hashlib.md5(key.encode('utf-8')).hexdigest()[:16]

    # ============================================================
    # 矛盾检测
    # ============================================================

    def _check_contradiction(self, new_fact: ExtractedFact):
        """检测新事实是否与已有事实矛盾"""
        # 查找同类主题的事实
        existing_facts = self.db.query(ExtractedFact).filter(
            ExtractedFact.project_id == new_fact.project_id,
            ExtractedFact.subject == new_fact.subject,
            ExtractedFact.fact_hash != new_fact.fact_hash,
            ExtractedFact.category == new_fact.category
        ).all()

        for existing in existing_facts:
            if self._is_contradiction(new_fact, existing):
                # 发现矛盾，记录
                self._record_contradiction(new_fact, existing)

    def _is_contradiction(self, fact_a: ExtractedFact, fact_b: ExtractedFact) -> bool:
        """
        判断两个事实是否矛盾
        简单逻辑：同主语、同类别、不同谓语
        """
        if fact_a.subject != fact_b.subject:
            return False
        if fact_a.category != fact_b.category:
            return False

        # 检查谓语是否互斥
        predicates = [fact_a.predicate, fact_b.predicate]

        # 互斥关键词检测
        contradictions = [
            # 生死互斥
            (["活着", "存活", "健康"], ["死亡", "死了", "已故"]),
            # 情绪互斥
            (["愤怒", "生气"], ["高兴", "开心", "快乐"]),
            (["悲伤", "伤心"], ["高兴", "开心"]),
            # 关系互斥
            (["敌人", "敌对"], ["朋友", "友好", "友善"]),
            (["爱人", "恋人"], ["陌生人"]),
            # 位置互斥（同一时间不能同时在两个地方）
            # 状态互斥
            (["知道", "了解"], ["不知道", "不了解"]),
        ]

        pred_a = fact_a.predicate
        pred_b = fact_b.predicate

        for group_a, group_b in contradictions:
            if any(w in pred_a for w in group_a) and any(w in pred_b for w in group_b):
                return True
            if any(w in pred_a for w in group_b) and any(w in pred_b for w in group_a):
                return True

        return False

    def _record_contradiction(
        self,
        fact_a: ExtractedFact,
        fact_b: ExtractedFact
    ):
        """记录矛盾"""
        # 确定矛盾类型
        if fact_a.category == "character_action":
            cont_type = "character_contradiction"
        elif fact_a.category == "world_event":
            cont_type = "world_contradiction"
        else:
            cont_type = "timeline_contradiction"

        contradiction = Contradiction(
            id=str(uuid.uuid4()),
            project_id=fact_a.project_id,
            fact_a_id=fact_a.id,
            fact_b_id=fact_b.id,
            fact_a_content=f"{fact_a.subject}: {fact_a.predicate}",
            fact_b_content=f"{fact_b.subject}: {fact_b.predicate}",
            contradiction_type=cont_type,
            severity="medium",
            status="detected",
            created_at=datetime.utcnow()
        )

        self.db.add(contradiction)
        self.db.commit()

    def get_project_contradictions(
        self,
        project_id: str,
        status: str = None
    ) -> list[Contradiction]:
        """获取项目的所有矛盾"""
        query = self.db.query(Contradiction).filter(
            Contradiction.project_id == project_id
        )
        if status:
            query = query.filter(Contradiction.status == status)
        return query.order_by(Contradiction.created_at.desc()).all()

    def resolve_contradiction(
        self,
        contradiction_id: str,
        resolution: str,
        resolved_fact_id: str = None
    ):
        """解决矛盾"""
        contradiction = self.db.query(Contradiction).filter(
            Contradiction.id == contradiction_id
        ).first()
        if contradiction:
            contradiction.status = "resolved"
            contradiction.resolution = resolution
            contradiction.resolved_at = datetime.utcnow()

            # 如果指定了解决的事实，让它覆盖旧事实
            if resolved_fact_id:
                resolved_fact = self.db.query(ExtractedFact).filter(
                    ExtractedFact.id == resolved_fact_id
                ).first()
                if resolved_fact:
                    # 将旧事实标记为低置信度
                    old_fact_ids = [contradiction.fact_a_id, contradiction.fact_b_id]
                    for fact_id in old_fact_ids:
                        if fact_id != resolved_fact_id:
                            old_fact = self.db.query(ExtractedFact).filter(
                                ExtractedFact.id == fact_id
                            ).first()
                            if old_fact:
                                old_fact.confidence = "low"

            self.db.commit()

    def ignore_contradiction(self, contradiction_id: str, reason: str):
        """忽略矛盾"""
        contradiction = self.db.query(Contradiction).filter(
            Contradiction.id == contradiction_id
        ).first()
        if contradiction:
            contradiction.status = "ignored"
            contradiction.resolution = reason
            self.db.commit()

    # ============================================================
    # 事实查询
    # ============================================================

    def get_character_facts(
        self,
        project_id: str,
        character_name: str,
        limit: int = 20
    ) -> list[ExtractedFact]:
        """获取角色的所有事实"""
        return self.db.query(ExtractedFact).filter(
            ExtractedFact.project_id == project_id,
            ExtractedFact.subject == character_name
        ).order_by(ExtractedFact.created_at.desc()).limit(limit).all()

    def get_category_facts(
        self,
        project_id: str,
        category: str,
        limit: int = 50
    ) -> list[ExtractedFact]:
        """获取某类别的所有事实"""
        return self.db.query(ExtractedFact).filter(
            ExtractedFact.project_id == project_id,
            ExtractedFact.category == category
        ).order_by(ExtractedFact.created_at.desc()).limit(limit).all()

    def get_latest_facts(
        self,
        project_id: str,
        limit: int = 30
    ) -> list[ExtractedFact]:
        """获取最新的事实"""
        return self.db.query(ExtractedFact).filter(
            ExtractedFact.project_id == project_id
        ).order_by(ExtractedFact.created_at.desc()).limit(limit).all()

    def get_fact_by_hash(
        self,
        project_id: str,
        fact_hash: str
    ) -> list[ExtractedFact]:
        """通过哈希查找事实"""
        return self.db.query(ExtractedFact).filter(
            ExtractedFact.project_id == project_id,
            ExtractedFact.fact_hash == fact_hash
        ).all()

    # ============================================================
    # 证据链构建
    # ============================================================

    def get_evidence_chain(self, fact_id: str) -> dict:
        """
        构建某个事实的证据链
        返回事实及其来源章节的信息
        """
        fact = self.db.query(ExtractedFact).filter(ExtractedFact.id == fact_id).first()
        if not fact:
            return {}

        chapter = self.db.query(Chapter).filter(Chapter.id == fact.chapter_id).first()

        return {
            "fact": fact,
            "chapter": chapter.number if chapter else None,
            "chapter_title": chapter.title if chapter else None,
            "evidence_text": fact.evidence_text
        }

    def format_facts_for_prompt(
        self,
        project_id: str,
        character_name: str = None,
        category: str = None
    ) -> str:
        """
        将事实格式化为prompt字符串
        用于在写作时传递已知事实
        """
        if character_name:
            facts = self.get_character_facts(project_id, character_name)
        elif category:
            facts = self.get_category_facts(project_id, category)
        else:
            facts = self.get_latest_facts(project_id)

        if not facts:
            return ""

        parts = ["【已知事实】"]
        for fact in facts[:10]:  # 限制数量
            conf_mark = "✓" if fact.confidence == "high" else "?"
            parts.append(f"{conf_mark} {fact.subject}: {fact.predicate}")

        return "\n".join(parts)

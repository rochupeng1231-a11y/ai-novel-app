# -*- coding: utf-8 -*-
"""
心智理论 (ToM) + 伏笔三元组 (CFPG)

ToM: 理解角色的心理状态（信念、意图）
CFPG: 管理伏笔的设置-触发-回收
"""
import uuid
import json
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from database.models import (
    Character, Chapter, Foreshadow,
    CharacterRelation
)


class MindTheory:
    """心智理论 - 角色心理状态追踪"""

    def __init__(self, db: Session):
        self.db = db

    def analyze_character_mind(
        self,
        character_id: str,
        chapter_content: str,
        chapter_id: str
    ) -> dict:
        """
        分析角色在章节中的心理状态
        实际由LLM分析，这里定义返回结构

        返回:
        {
            "belief_about_self": "对自己的认知",
            "belief_about_others": {"角色A": "认知", "角色B": "认知"},
            "intention": "当前意图",
            "hidden_knowledge": ["秘密1", "秘密2"],
            "emotional_state": "情绪状态",
            "mental_barriers": "心理防线"
        }
        """
        # 实际由LLM填充
        return {}

    def update_mind_from_llm(
        self,
        character_id: str,
        chapter_id: str,
        mind_data: dict
    ):
        """从LLM分析结果更新心理状态"""
        # 这里可以存储到专门的表，或合并到CharacterState
        # 简化处理：存储到Character表的扩展字段
        char = self.db.query(Character).filter(Character.id == character_id).first()
        if not char:
            return

        # 将mind_data转为JSON存储在personality或其他字段
        # 这里简化处理，实际可能需要专门表
        pass

    def get_beliefs_about_others(
        self,
        character_id: str
    ) -> dict:
        """
        获取角色对他人的认知
        用于写作时理解角色为什么会做出某些行为
        """
        # 从角色关系中获取基本信息
        relations = self.db.query(CharacterRelation).filter(
            CharacterRelation.character_a_id == character_id
        ).all()

        beliefs = {}
        for rel in relations:
            char_b = self.db.query(Character).filter(
                Character.id == rel.character_b_id
            ).first()
            if char_b:
                beliefs[char_b.name] = {
                    "relation": rel.relation_type,
                    "description": rel.description or ""
                }

        return beliefs

    def format_mind_context(
        self,
        character_id: str,
        chapter_number: int = None
    ) -> str:
        """
        格式化心理状态上下文用于prompt
        """
        char = self.db.query(Character).filter(Character.id == character_id).first()
        if not char:
            return ""

        parts = [f"【{char.name}的心理】"]

        # 关系认知
        beliefs = self.get_beliefs_about_others(character_id)
        if beliefs:
            parts.append("对他人的认知:")
            for other_name, info in beliefs.items():
                parts.append(f"  - {other_name}: {info['relation']}")
                if info['description']:
                    parts.append(f"    ({info['description']})")

        return "\n".join(parts)


class ForeshadowManager:
    """伏笔三元组管理器 (CFPG)"""

    def __init__(self, db: Session):
        self.db = db

    def create_foreshadow_triplet(
        self,
        project_id: str,
        setup_chapter_id: str,
        clue_text: str,
        trigger_condition: str = None,
        keywords: list = None
    ) -> dict:
        """
        创建伏笔三元组
        setup -> trigger -> resolve
        """
        triplet = Foreshadow(
            id=str(uuid.uuid4()),
            project_id=project_id,
            chapter_id=setup_chapter_id,
            keyword=",".join(keywords) if keywords else clue_text[:50],
            description=clue_text,
            status="planted"
        )

        self.db.add(triplet)
        self.db.commit()
        self.db.refresh(triplet)

        return {
            "id": triplet.id,
            "status": triplet.status,
            "clue_text": clue_text,
            "setup_chapter_id": setup_chapter_id
        }

    def plant_foreshadow_from_outline(
        self,
        project_id: str,
        outline: str,
        first_chapter_id: str
    ) -> list[dict]:
        """
        从大纲中识别并埋设伏笔
        实际由LLM分析大纲，识别伏笔意图
        """
        planted = []

        # 简化处理：从大纲文本中提取潜在伏笔
        # 实际需要LLM分析
        foreshadow_keywords = ["伏笔", "预示", "暗示", "之后会发现", "原来"]

        lines = outline.split("\n")
        for i, line in enumerate(lines):
            for keyword in foreshadow_keywords:
                if keyword in line:
                    # 简单处理：认为这是一个伏笔提示
                    triplet = self.create_foreshadow_triplet(
                        project_id=project_id,
                        setup_chapter_id=first_chapter_id,
                        clue_text=line.strip(),
                        keywords=[keyword]
                    )
                    planted.append(triplet)
                    break

        return planted

    def get_planted_foreshadows(
        self,
        project_id: str,
        status: str = "planted"
    ) -> list[Foreshadow]:
        """获取已埋设的伏笔"""
        return self.db.query(Foreshadow).filter(
            Foreshadow.project_id == project_id,
            Foreshadow.status == status
        ).all()

    def get_pending_triggers(
        self,
        project_id: str,
        current_chapter_number: int
    ) -> list[Foreshadow]:
        """
        获取即将需要触发的伏笔
        根据伏笔的埋设章节和触发条件判断
        """
        planted = self.get_planted_foreshadows(project_id, "planted")

        pending = []
        for fs in planted:
            chapter = self.db.query(Chapter).filter(Chapter.id == fs.chapter_id).first()
            if chapter and chapter.number < current_chapter_number:
                # 伏笔埋设在当前章节之前，应该考虑触发
                pending.append(fs)

        return pending

    def trigger_foreshadow(
        self,
        foreshadow_id: str,
        trigger_chapter_id: str = None
    ):
        """触发伏笔"""
        fs = self.db.query(Foreshadow).filter(Foreshadow.id == foreshadow_id).first()
        if fs:
            fs.status = "triggered"
            if trigger_chapter_id:
                fs.chapter_id = trigger_chapter_id
            self.db.commit()

    def resolve_foreshadow(
        self,
        foreshadow_id: str,
        resolve_text: str = None,
        resolve_chapter_id: str = None
    ):
        """回收伏笔"""
        fs = self.db.query(Foreshadow).filter(Foreshadow.id == foreshadow_id).first()
        if fs:
            fs.status = "resolved"
            if resolve_text:
                fs.description = resolve_text
            if resolve_chapter_id:
                fs.chapter_id = resolve_chapter_id
            fs.resolved_at = datetime.utcnow()
            self.db.commit()

    def format_foreshadow_context(
        self,
        project_id: str,
        current_chapter_number: int
    ) -> str:
        """
        格式化伏笔上下文用于prompt
        告诉AI有哪些伏笔需要注意
        """
        # 获取已埋设但未触发的伏笔
        planted = self.get_planted_foreshadows(project_id, "planted")
        triggered = self.get_planted_foreshadows(project_id, "triggered")

        parts = []

        if planted:
            parts.append("【待触发伏笔】")
            for fs in planted:
                chapter = self.db.query(Chapter).filter(
                    Chapter.id == fs.chapter_id
                ).first()
                ch_num = chapter.number if chapter else "?"
                parts.append(f"  - 第{ch_num}章埋设: {fs.keyword}")

        if triggered:
            parts.append("\n【已触发伏笔】")
            for fs in triggered:
                chapter = self.db.query(Chapter).filter(
                    Chapter.id == fs.chapter_id
                ).first()
                ch_num = chapter.number if chapter else "?"
                parts.append(f"  - 第{ch_num}章已触发: {fs.keyword}")

        return "\n".join(parts) if parts else ""

    def check_foreshadow_in_content(
        self,
        foreshadow_id: str,
        content: str
    ) -> bool:
        """
        检查内容是否包含伏笔关键词
        用于判断伏笔是否被自然地触发或回收
        """
        fs = self.db.query(Foreshadow).filter(Foreshadow.id == foreshadow_id).first()
        if not fs:
            return False

        keywords = fs.keyword.split(",")
        content_lower = content.lower()

        for keyword in keywords:
            if keyword.strip().lower() in content_lower:
                return True

        return False

    def get_foreshadow_statistics(self, project_id: str) -> dict:
        """获取伏笔统计"""
        all_fs = self.db.query(Foreshadow).filter(
            Foreshadow.project_id == project_id
        ).all()

        planted = len([f for f in all_fs if f.status == "planted"])
        triggered = len([f for f in all_fs if f.status == "triggered"])
        resolved = len([f for f in all_fs if f.status == "resolved"])

        return {
            "total": len(all_fs),
            "planted": planted,
            "triggered": triggered,
            "resolved": resolved,
            "resolution_rate": f"{resolved/(len(all_fs) or 1)*100:.1f}%"
        }

# -*- coding: utf-8 -*-
"""
ConStory-Checker 情节一致性检验器

在写新章节前检验即将生成的内容是否会与已发生的事实矛盾
"""
import json
from typing import Optional
from sqlalchemy.orm import Session
from database.models import ExtractedFact, Contradiction, CharacterState, Chapter, Character


class ConsistencyChecker:
    """情节一致性检验器"""

    def __init__(self, db: Session):
        self.db = db

    def pre_write_check(
        self,
        project_id: str,
        new_chapter_plan: dict = None
    ) -> list[dict]:
        """
        写前检验
        检查新章节是否会与已有事实矛盾

        new_chapter_plan: 新章节的计划，包含:
        {
            "planned_events": ["事件1", "事件2"],
            "planned_character_states": {"角色名": "预期状态"},
            "planned_dialogues": ["对话1", "对话2"]
        }

        返回警告列表:
        [
            {
                "type": "contradiction",
                "severity": "high",
                "message": "...",
                "conflicts_with": "事实: xxx",
                "suggestion": "..."
            },
            ...
        ]
        """
        warnings = []

        # 1. 检查角色状态矛盾
        warnings.extend(self._check_character_state_contradictions(project_id))

        # 2. 检查时间线矛盾
        warnings.extend(self._check_timeline_contradictions(project_id))

        # 3. 检查已死亡/消失角色
        warnings.extend(self._check_dead_character_usage(project_id))

        # 4. 如果有新章节计划，检查计划中的事件
        if new_chapter_plan:
            warnings.extend(self._check_planned_events(project_id, new_chapter_plan))

        return warnings

    def _check_character_state_contradictions(self, project_id: str) -> list[dict]:
        """检查角色状态矛盾"""
        warnings = []

        # 获取当前角色状态
        char_states = self.db.query(CharacterState).filter(
            CharacterState.project_id == project_id
        ).all()

        for state in char_states:
            # 检查死亡角色
            if state.status == "dead":
                warnings.append({
                    "type": "character_status",
                    "severity": "high",
                    "character": state.character_id,
                    "message": f"角色 {state.character_id} 已经死亡",
                    "conflicts_with": "当前状态: dead",
                    "suggestion": "如果需要使用该角色，考虑用回忆/幽灵等形式"
                })

            # 检查不位置冲突（基于时间）
            # 这里简化处理，实际需要更复杂的逻辑

        return warnings

    def _check_timeline_contradictions(self, project_id: str) -> list[dict]:
        """检查时间线矛盾"""
        warnings = []

        # 获取已解决的矛盾
        contradictions = self.db.query(Contradiction).filter(
            Contradiction.project_id == project_id,
            Contradiction.status == "detected"
        ).all()

        for cont in contradictions:
            warnings.append({
                "type": "timeline_contradiction",
                "severity": cont.severity,
                "message": f"检测到未解决的矛盾: {cont.fact_a_content} vs {cont.fact_b_content}",
                "conflicts_with": f"{cont.fact_a_content} | {cont.fact_b_content}",
                "suggestion": "请确认哪个事实是正确的，或在回复中说明如何解决"
            })

        return warnings

    def _check_dead_character_usage(self, project_id: str) -> list[dict]:
        """检查是否使用了已死亡的角色"""
        warnings = []

        dead_states = self.db.query(CharacterState).filter(
            CharacterState.project_id == project_id,
            CharacterState.status == "dead"
        ).all()

        for state in dead_states:
            char = self.db.query(Character).filter(Character.id == state.character_id).first()
            if char:
                warnings.append({
                    "type": "dead_character",
                    "severity": "high",
                    "character": char.name,
                    "message": f"角色 {char.name} 已死亡，不应出现在正常场景中",
                    "suggestion": "如需出现，考虑使用: 回忆/幻觉/鬼魂/后代等设定"
                })

        return warnings

    def _check_planned_events(
        self,
        project_id: str,
        new_chapter_plan: dict
    ) -> list[dict]:
        """检查新章节计划中的事件"""
        warnings = []

        planned_events = new_chapter_plan.get("planned_events", [])
        planned_char_states = new_chapter_plan.get("planned_character_states", {})

        # 检查计划中的角色状态
        for char_name, planned_state in planned_char_states.items():
            # 获取该角色当前状态
            char = self.db.query(Character).filter(
                Character.project_id == project_id,
                Character.name == char_name
            ).first()

            if not char:
                continue

            state = self.db.query(CharacterState).filter(
                CharacterState.character_id == char.id
            ).first()

            if state and state.status == "dead" and "死亡" not in planned_state:
                warnings.append({
                    "type": "planned_contradiction",
                    "severity": "high",
                    "character": char_name,
                    "message": f"计划让已死亡的角色 {char_name} 出现在: {planned_state}",
                    "conflicts_with": f"当前状态: dead",
                    "suggestion": "请修改计划或调整角色状态"
                })

        return warnings

    def check_continuity(
        self,
        project_id: str,
        previous_chapter_id: str,
        new_content: str
    ) -> dict:
        """
        检查新内容是否与上一章衔接

        返回:
        {
            "is_continuable": true/false,
            "issues": [...],
            "suggestions": [...]
        }
        """
        issues = []
        suggestions = []

        # 获取上一章的角色状态
        prev_chapter = self.db.query(Chapter).filter(
            Chapter.id == previous_chapter_id
        ).first()

        if not prev_chapter:
            issues.append("无法找到上一章")
            return {"is_continuable": False, "issues": issues, "suggestions": suggestions}

        # 检查新内容是否提到了应该在的角色
        # 这里简化处理，实际需要LLM分析

        return {
            "is_continuable": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions
        }

    def get_consistency_report(self, project_id: str) -> dict:
        """
        获取项目的整体一致性报告
        """
        # 统计矛盾数量
        contradictions = self.db.query(Contradiction).filter(
            Contradiction.project_id == project_id
        ).all()

        # 按状态分类
        detected = [c for c in contradictions if c.status == "detected"]
        resolved = [c for c in contradictions if c.status == "resolved"]
        ignored = [c for c in contradictions if c.status == "ignored"]

        # 统计角色状态
        char_states = self.db.query(CharacterState).filter(
            CharacterState.project_id == project_id
        ).all()
        dead_count = len([s for s in char_states if s.status == "dead"])
        active_count = len([s for s in char_states if s.status == "active"])

        return {
            "total_contradictions": len(contradictions),
            "detected": len(detected),
            "resolved": len(resolved),
            "ignored": len(ignored),
            "dead_characters": dead_count,
            "active_characters": active_count,
            "has_issues": len(detected) > 0
        }

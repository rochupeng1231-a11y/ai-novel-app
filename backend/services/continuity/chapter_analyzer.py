# -*- coding: utf-8 -*-
"""
LLM章节分析服务

章节写完后，调用LLM分析内容并更新各种状态
"""
import json
import re
from typing import Optional
from sqlalchemy.orm import Session
from database.models import Chapter, Character, Project


class ChapterAnalyzer:
    """
    章节内容分析器

    负责调用LLM分析章节，提取：
    - 时间线事件
    - 角色状态变化
    - 事实与矛盾
    - 角色心智
    """

    def __init__(self, db: Session):
        self.db = db

    def analyze_chapter(
        self,
        chapter_id: str,
        chapter_content: str = None
    ) -> dict:
        """
        分析章节内容

        Returns:
            {
                "timeline_events": [...],
                "character_states": {...},
                "facts": [...],
                "character_minds": {...},
                "trope_usage": [...],
                "success": bool,
                "error": str
            }
        """
        chapter = self.db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if not chapter:
            return {"success": False, "error": "章节不存在"}

        if not chapter_content:
            chapter_content = chapter.content

        if not chapter_content:
            return {"success": False, "error": "章节内容为空"}

        project = self.db.query(Project).filter(Project.id == chapter.project_id).first()
        if not project:
            return {"success": False, "error": "项目不存在"}

        # 构建分析prompt
        analysis_prompt = self._build_analysis_prompt(chapter, chapter_content, project)

        # 调用LLM分析（这里使用同步方式，实际可能是异步）
        # 由于当前项目使用流式API，这里需要单独调用
        # 我们先用规则方式做基础分析，LLM部分留作扩展
        result = self._basic_analysis(chapter, chapter_content, project)

        return result

    def _build_analysis_prompt(
        self,
        chapter: Chapter,
        content: str,
        project: Project
    ) -> str:
        """构建分析prompt"""
        # 获取角色列表
        characters = self.db.query(Character).filter(
            Character.project_id == project.id
        ).all()
        char_names = [c.name for c in characters]

        prompt = f"""你是一个小说分析专家。请分析以下章节内容，提取结构化信息。

【小说类型】{project.novel_type or '未指定'}
【章节】第{chapter.number}章：{chapter.title}

【已知角色】{', '.join(char_names) if char_names else '无'}

【章节内容】
{content[:3000]}

请提取以下信息（JSON格式）：

1. 时间线事件（最多5个重要事件）:
   - event_type: action/dialogue/state_change/emotion_change
   - content: 事件描述（30字内）
   - importance: high/normal
   - characters_involved: 涉及的角色名列表

2. 角色状态变化:
   - 角色名: {new_location, new_emotion, new_physical, new_goal}

3. 关键事实（最多10个）:
   - category: character_action/dialogue/world_event/setting
   - subject: 主语
   - predicate: 谓语（30字内）
   - evidence_text: 原文摘录（20字内）

4. 套路使用检测:
   - 检测到的套路列表

请直接输出JSON，不要其他内容。"""

        return prompt

    def _basic_analysis(
        self,
        chapter: Chapter,
        content: str,
        project: Project
    ) -> dict:
        """
        基础分析（规则方式）

        用于没有LLM调用能力时的降级方案
        实际产品中应使用真实LLM分析
        """
        result = {
            "timeline_events": [],
            "character_states": {},
            "facts": [],
            "character_minds": {},
            "trope_usage": [],
            "success": True
        }

        # 简化：只提取基本的事件类型统计
        # 动作描写
        action_patterns = [
            "打", "杀", "攻击", "拿出", "拿起", "走向", "推", "拉", "打开"
        ]
        dialogue_patterns = [
            "说", "问", "答", "喊道", "低声道", "笑着说"
        ]

        action_count = sum(1 for p in action_patterns if p in content)
        dialogue_count = sum(1 for p in dialogue_patterns if p in content)

        # 添加基础事件
        if action_count > 0 or dialogue_count > 0:
            result["timeline_events"].append({
                "event_type": "mixed",
                "content": f"动作描写{action_count}处，对话{dialogue_count}处",
                "importance": "normal",
                "characters_involved": []
            })

        # 提取引号内容作为对话事实
        dialogues = re.findall(r'[""\']([^""\']{5,50})[""\']', content)
        for i, d in enumerate(dialogues[:5]):
            result["facts"].append({
                "category": "dialogue",
                "subject": "角色",
                "predicate": f"说：{d[:20]}",
                "evidence_text": d[:30]
            })

        return result

    def analyze_with_llm(self, chapter_id: str, chapter_content: str = None) -> dict:
        """
        使用LLM进行完整分析

        这个方法需要调用AI服务
        暂未实现，保留接口
        """
        # TODO: 调用AI进行完整分析
        # 需要实现：
        # 1. 构建分析prompt
        # 2. 调用AI服务
        # 3. 解析返回的JSON
        # 4. 存储到对应表
        pass


class LLMWritingAdvisor:
    """
    LLM写作顾问

    在写作前提供建议，写作后提供反馈
    """

    def __init__(self, db: Session):
        self.db = db

    def get_continuity_suggestion(
        self,
        project_id: str,
        chapter_number: int,
        previous_summary: str
    ) -> str:
        """
        获取衔接建议

        告诉LLM如何自然衔接上一章
        """
        prompt = f"""作为小说写作顾问，请为第{chapter_number}章提供衔接建议。

【上一章摘要】
{previous_summary[:500] if previous_summary else '无'}

请提供：
1. 自然衔接的关键点
2. 角色状态延续
3. 情节推进建议

直接输出建议，不要其他格式。"""

        # 基础返回，实际应调用LLM
        suggestions = []
        if previous_summary:
            suggestions.append("延续上一章的节奏和氛围")
            suggestions.append("确保角色状态与上章结尾一致")
            suggestions.append("自然引入本章新的冲突或发展")

        return "\n".join(suggestions) if suggestions else "承接上文，自然发展"

    def get_foreshadow_reminder(
        self,
        project_id: str,
        chapter_number: int
    ) -> list[str]:
        """
        获取伏笔提醒

        哪些伏笔应该在这章被触发或埋设
        """
        # TODO: 从数据库查询待触发伏笔
        return []

    def check_plot_continuity(
        self,
        new_content: str,
        previous_summary: str,
        character_states: dict
    ) -> dict:
        """
        检查情节连贯性

        Returns:
            {
                "is_continious": bool,
                "issues": [...],
                "suggestions": [...]
            }
        """
        issues = []
        suggestions = []

        # 简单检查：角色名是否一致
        # 实际需要更复杂的LLM分析

        return {
            "is_continious": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions
        }

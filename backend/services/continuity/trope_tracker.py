# -*- coding: utf-8 -*-
"""
CoKe 关键词防套话系统

防止AI重复使用固定套路，保持文风新鲜
"""
import json
from collections import defaultdict
from sqlalchemy.orm import Session
from database.models import Chapter


class TropeTracker:
    """套路追踪器"""

    # 默认黑名单 - 常见套路词
    DEFAULT_BLACKLIST = [
        "英雄救美",
        "命中注定",
        "突然顿悟",
        "恍然大悟",
        "两情相悦",
        "深情对视",
        "欲言又止",
        "不约而同",
        "心照不宣",
        "理所当然",
        "不由自主",
        "不由自主地",
        "不由自主",
        "情不自禁",
        "理所当然",
        "脱口而出",
        "掩嘴轻笑",
        "盈盈一笑",
        "浅浅一笑",
        "淡淡一笑",
        "嘴角上扬",
        "眉头微皱",
        "眼神复杂",
        "若有所思",
        "意味深长",
        "邪魅一笑",
        "轻蔑一笑",
        "冷哼一声",
    ]

    # 白名单 - 某些类型必须使用的
    DEFAULT_WHITELIST = []

    def __init__(self, db: Session):
        self.db = db
        self.project_tropes = {}  # {project_id: {trope: count}}
        self.project_blacklist = {}  # {project_id: [trope1, trope2]}

    def extract_tropes_from_chapter(self, chapter_content: str) -> list[str]:
        """
        从章节内容中提取使用的套路
        返回检测到的套路列表
        实际由LLM提取，这里返回结构
        """
        detected = []
        for trope in self.DEFAULT_BLACKLIST:
            if trope in chapter_content:
                detected.append(trope)
        return detected

    def record_trope_usage(
        self,
        project_id: str,
        chapter_id: str,
        tropes: list[str]
    ):
        """记录套路使用"""
        if project_id not in self.project_tropes:
            self.project_tropes[project_id] = defaultdict(int)

        for trope in tropes:
            self.project_tropes[project_id][trope] += 1

    def get_overused_tropes(
        self,
        project_id: str,
        threshold: int = 3
    ) -> list[tuple[str, int]]:
        """
        获取过度使用的套路
        threshold: 使用次数超过此值认为是过度使用
        返回: [(trope, count), ...]
        """
        if project_id not in self.project_tropes:
            return []

        overused = [
            (trope, count)
            for trope, count in self.project_tropes[project_id].items()
            if count >= threshold
        ]
        return sorted(overused, key=lambda x: x[1], reverse=True)

    def get_trope_warning_for_chapter(
        self,
        project_id: str,
        chapter_number: int
    ) -> str:
        """
        获取章节的套路警告
        返回格式化的警告字符串
        """
        overused = self.get_overused_tropes(project_id, threshold=2)

        if not overused:
            return ""

        parts = ["【套路警告】已过度使用的表达，请尽量避免:"]
        for trope, count in overused[:5]:  # 最多5个
            parts.append(f"  - {trope} (已用{count}次)")

        return "\n".join(parts)

    def should_regenerate_for_trope(
        self,
        chapter_content: str,
        project_id: str,
        threshold: int = 3
    ) -> tuple[bool, str]:
        """
        检查是否因为套路过度使用需要重生成

        返回: (should_regenerate, reason)
        """
        detected = self.extract_tropes_from_chapter(chapter_content)
        overused = self.get_overused_tropes(project_id, threshold)

        if not overused:
            return False, ""

        # 检查是否有过度使用的套路
        problematic = []
        for trope in detected:
            for overused_trope, count in overused:
                if trope == overused_trope:
                    problematic.append(trope)

        if problematic:
            return True, f"使用了过度使用的套路: {', '.join(problematic)}"

        return False, ""

    def add_to_blacklist(self, project_id: str, tropes: list[str]):
        """为项目添加黑名单"""
        if project_id not in self.project_blacklist:
            self.project_blacklist[project_id] = set(self.DEFAULT_BLACKLIST)
        self.project_blacklist[project_id].update(tropes)

    def remove_from_blacklist(self, project_id: str, tropes: list[str]):
        """从项目黑名单移除"""
        if project_id in self.project_blacklist:
            self.project_blacklist[project_id].difference_update(tropes)

    def get_blacklist(self, project_id: str) -> list[str]:
        """获取项目的黑名单"""
        if project_id in self.project_blacklist:
            return list(self.project_blacklist[project_id])
        return self.DEFAULT_BLACKLIST.copy()

    def format_trope_instruction(
        self,
        project_id: str,
        chapter_number: int
    ) -> str:
        """
        格式化为prompt的套路指令
        """
        blacklist = self.get_blacklist(project_id)
        overused = self.get_overused_tropes(project_id, threshold=2)

        parts = []

        # 如果有过度使用的，单独警告
        if overused:
            parts.append("【避免重复】以下表达已过度使用，请用新鲜方式表达:")
            for trope, count in overused[:5]:
                parts.append(f"  - {trope}")
            parts.append("")

        # 黑名单（如果与overused不同）
        not_yet_overused = [t for t in blacklist if not any(t == o[0] for o in overused)]
        if not_yet_overused and len(not_yet_overused) > 0:
            # 只展示部分，不全部列出
            parts.append("【慎用表达】以下套路表达建议少用:")
            parts.append(f"  {', '.join(not_yet_overused[:10])}...")

        return "\n".join(parts)

    def get_trope_statistics(self, project_id: str) -> dict:
        """获取项目的套路统计"""
        if project_id not in self.project_tropes:
            return {"total_types": 0, "total_uses": 0, "top_tropes": []}

        tropes = self.project_tropes[project_id]
        total_uses = sum(tropes.values())
        top = sorted(tropes.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "total_types": len(tropes),
            "total_uses": total_uses,
            "top_tropes": [{"trope": t, "count": c} for t, c in top]
        }

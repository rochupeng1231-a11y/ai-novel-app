# -*- coding: utf-8 -*-
"""
BVSR/SWAG 生成控制

BVSR (Betavariate Stochastic Sampling with Randomness): 随机性
SWAG (Semantic-Guided Action): 确定性动作引导
"""
import random
from typing import Optional


class GenerationController:
    """
    生成控制器

    BVSR模式: 使用随机采样，保持创意
    SWAG模式: 确保关键情节按计划执行
    """

    def __init__(
        self,
        temperature: float = 0.7,
        bvsr_enabled: bool = True,
        swag_anchors: list = None
    ):
        """
        初始化生成控制器

        Args:
            temperature: 创造性参数 (0-1)
            bvsr_enabled: 是否启用BVSR随机模式
            swag_anchors: 必须包含的关键事件列表
        """
        self.temperature = temperature
        self.bvsr_enabled = bvsr_enabled
        self.swag_anchors = swag_anchors or []
        self.swag_must_include = []  # 必须包含的事件

    def add_swag_anchor(self, anchor_event: str, must_include: bool = False):
        """
        添加确定性锚点

        Args:
            anchor_event: 锚点描述，如"主角获得宝剑"
            must_include: 是否必须在内容中出现
        """
        if anchor_event not in self.swag_anchors:
            self.swag_anchors.append(anchor_event)
        if must_include and anchor_event not in self.swag_must_include:
            self.swag_must_include.append(anchor_event)

    def remove_swag_anchor(self, anchor_event: str):
        """移除锚点"""
        if anchor_event in self.swag_anchors:
            self.swag_anchors.remove(anchor_event)
        if anchor_event in self.swag_must_include:
            self.swag_must_include.remove(anchor_event)

    def get_temperature(self) -> float:
        """
        根据模式获取实际temperature
        BVSR模式可以动态调整
        """
        if self.bvsr_enabled:
            # 基础随机性 + 一点波动
            return self.temperature + random.uniform(-0.1, 0.1)
        return self.temperature * 0.5  # 更确定性

    def build_prompt_with_swag(
        self,
        base_prompt: str,
        context: dict = None
    ) -> str:
        """
        将SWAG锚点加入prompt

        Args:
            base_prompt: 基础prompt
            context: 上下文信息

        Returns:
            添加了SWAG指令的prompt
        """
        if not self.swag_anchors:
            return base_prompt

        parts = [base_prompt]

        # 添加锚点指令
        if self.swag_anchors:
            parts.append("\n\n【关键事件】以下事件必须在内容中出现:")
            for anchor in self.swag_anchors:
                must = "(必须)" if anchor in self.swag_must_include else ""
                parts.append(f"  - {anchor} {must}")

        # 添加链接词（让锚点更自然地融入）
        if self.swag_anchors:
            parts.append("\n请确保以上事件自然融入故事，不生硬突兀。")

        return "\n".join(parts)

    def should_regenerate(self, generated_content: str) -> tuple[bool, str]:
        """
        判断是否需要重生成

        Returns:
            (should_regenerate, reason)
        """
        if not self.swag_must_include:
            return False, ""

        missing = []
        for anchor in self.swag_must_include:
            # 简单检查：锚点关键词是否出现在内容中
            # 实际可以更复杂：检查是否在关键位置出现
            if anchor not in generated_content:
                missing.append(anchor)

        if missing:
            return True, f"缺少必须包含的事件: {', '.join(missing)}"

        return False, ""

    def get_regeneration_suggestion(
        self,
        missing_anchor: str,
        context: dict = None
    ) -> str:
        """
        获取重生成建议
        告诉AI如何更好地包含这个事件
        """
        suggestions = {
            "主角获得宝剑": "考虑在情节中安排主角进入一个遗迹/宝箱/赠与等场景，自然获得宝剑",
            "角色死亡": "考虑安排角色在冲突中被击败，或为救他人而牺牲",
            "揭露秘密": "考虑安排角色在对话/回忆/文件中自然揭露秘密",
        }

        base = suggestions.get(missing_anchor, f"请确保将「{missing_anchor}」融入故事")

        if context:
            # 加入上下文帮助
            char_name = context.get("main_character", "主角")
            base += f"，结合{char_name}的当前处境"

        return base

    def enable_bvsr(self):
        """启用BVSR模式"""
        self.bvsr_enabled = True

    def disable_bvsr(self):
        """禁用BVSR模式（完全确定性）"""
        self.bvsr_enabled = False

    def get_swag_status(self) -> dict:
        """获取SWAG状态"""
        return {
            "total_anchors": len(self.swag_anchors),
            "must_include": len(self.swag_must_include),
            "anchors": self.swag_anchors,
            "bvsr_enabled": self.bvsr_enabled,
            "temperature": self.temperature
        }


class ChapterPlanValidator:
    """章节计划验证器 - 验证用户输入的章节计划"""

    def __init__(self):
        self.required_fields = ["title", "main_events"]
        self.optional_fields = ["character_states", "foreshadows"]

    def validate(self, chapter_plan: dict) -> tuple[bool, list]:
        """
        验证章节计划

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        # 检查必填字段
        for field in self.required_fields:
            if field not in chapter_plan:
                errors.append(f"缺少必填字段: {field}")

        # 检查main_events格式
        if "main_events" in chapter_plan:
            events = chapter_plan["main_events"]
            if not isinstance(events, list):
                errors.append("main_events必须是列表")
            elif len(events) == 0:
                errors.append("main_events不能为空")

        return len(errors) == 0, errors

    def extract_swag_anchors(self, chapter_plan: dict) -> list[dict]:
        """
        从章节计划中提取SWAG锚点

        Returns:
            [{"event": str, "must_include": bool}, ...]
        """
        anchors = []

        main_events = chapter_plan.get("main_events", [])
        for event in main_events:
            if isinstance(event, str):
                anchors.append({"event": event, "must_include": True})
            elif isinstance(event, dict):
                anchors.append({
                    "event": event.get("description", ""),
                    "must_include": event.get("must_include", False)
                })

        return anchors

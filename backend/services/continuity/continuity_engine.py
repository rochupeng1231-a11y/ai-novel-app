# -*- coding: utf-8 -*-
"""
ContinuityEngine - 统一入口，编排所有模块

这是向外部提供服务的统一接口
"""
from typing import Optional
from sqlalchemy.orm import Session
from .timeline_graph import TimelineGraph
from .state_tracker import StateTracker
from .fact_extractor import FactExtractor
from .consistency_checker import ConsistencyChecker
from .trope_tracker import TropeTracker
from .mind_theory import MindTheory, ForeshadowManager
from .generation_controller import GenerationController


class ContinuityEngine:
    """
    章节衔接与一致性引擎

    整合所有模块，向写作流程提供统一服务
    """

    def __init__(self, db: Session):
        self.db = db
        self.timeline = TimelineGraph(db)
        self.state_tracker = StateTracker(db)
        self.fact_extractor = FactExtractor(db)
        self.consistency_checker = ConsistencyChecker(db)
        self.trope_tracker = TropeTracker(db)
        self.mind_theory = MindTheory(db)
        self.foreshadow_manager = ForeshadowManager(db)
        self.generation_controller = GenerationController()

    # ============================================================
    # 写前准备 - 生成写作上下文
    # ============================================================

    def prepare_writing_context(
        self,
        project_id: str,
        chapter_id: str,
        chapter_number: int
    ) -> dict:
        """
        准备写作所需的完整上下文

        Returns:
            {
                "character_states": {...},
                "world_state": {...},
                "previous_context": "...",
                "foreshadow_context": "...",
                "trope_warning": "...",
                "consistency_warnings": [...],
                "generation_instructions": "..."
            }
        """
        context = {}

        # 1. 角色状态 (SCORE)
        context["character_states"] = self.state_tracker.format_context_for_prompt(
            project_id, chapter_id
        )

        # 2. 世界状态
        world = self.state_tracker.get_world_state(project_id)
        if world:
            context["world_state"] = {
                "current_arc": world.current_arc,
                "main_conflict": world.main_conflict,
                "timeline_progress": world.timeline_progress
            }

        # 3. 上一章结尾上下文 (DOME)
        prev_context = self.timeline.get_last_n_chapters_context(
            project_id, chapter_id, n=1
        )

        # 优先使用事件摘要，如果没有事件则使用实际章节内容
        event_summary = prev_context.get("summary", "")
        chapter_content = prev_context.get("prev_chapter_content", "")

        print(f"[ContinuityEngine] 事件摘要长度: {len(event_summary)}, 章节内容长度: {len(chapter_content)}")

        if event_summary:
            context["previous_context"] = event_summary
        elif chapter_content:
            # 没有事件记录时，用实际内容作为上下文
            # 截取最后500字作为上一章结尾
            context["previous_context"] = f"（上章内容摘要）\n{chapter_content[-500:]}"
            print(f"[ContinuityEngine] 使用章节内容作为上下文，截取末尾500字")
        else:
            context["previous_context"] = ""
            print(f"[ContinuityEngine] 警告：既没有事件也没有章节内容")

        context["recent_events"] = [
            {"content": e.content, "type": e.event_type}
            for e in prev_context.get("last_chapter_events", [])
        ]

        # 4. 下一章预告（如果可用）
        # context["next_chapter_preview"] = ...

        # 5. 伏笔上下文 (CFPG)
        context["foreshadow_context"] = self.foreshadow_manager.format_foreshadow_context(
            project_id, chapter_number
        )

        # 6. 套路警告 (CoKe)
        context["trope_warning"] = self.trope_tracker.get_trope_warning_for_chapter(
            project_id, chapter_number
        )

        # 7. 一致性检查警告 (ConStory-Checker)
        warnings = self.consistency_checker.pre_write_check(project_id)
        context["consistency_warnings"] = warnings
        context["consistency_report"] = self.consistency_checker.get_consistency_report(project_id)

        return context

    def build_writing_prompt(
        self,
        project_id: str,
        chapter_id: str,
        chapter_number: int,
        base_instruction: str,
        additional_context: str = None
    ) -> str:
        """
        构建完整的写作prompt

        整合所有上下文信息
        """
        ctx = self.prepare_writing_context(project_id, chapter_id, chapter_number)

        parts = [base_instruction]

        # 添加角色状态
        if ctx.get("character_states"):
            parts.append("\n\n" + ctx["character_states"])

        # 添加上一章结尾
        if ctx.get("previous_context"):
            parts.append("\n\n【上一章结尾】")
            parts.append(ctx["previous_context"])

        # 添加伏笔上下文
        if ctx.get("foreshadow_context"):
            parts.append("\n\n" + ctx["foreshadow_context"])

        # 添加套路警告
        if ctx.get("trope_warning"):
            parts.append("\n\n" + ctx["trope_warning"])

        # 添加一致性警告
        if ctx.get("consistency_warnings"):
            parts.append("\n\n【一致性注意】")
            for warning in ctx["consistency_warnings"]:
                if warning["severity"] == "high":
                    parts.append(f"  ⚠ {warning['message']}")

        # 添加额外上下文
        if additional_context:
            parts.append("\n\n" + additional_context)

        # 应用SWAG锚点
        prompt = "\n".join(parts)
        prompt = self.generation_controller.build_prompt_with_swag(prompt, ctx)

        return prompt

    # ============================================================
    # 写后处理 - 更新状态
    # ============================================================

    def process_completed_chapter(
        self,
        project_id: str,
        chapter_id: str,
        chapter_content: str,
        chapter_number: int
    ):
        """
        章节写完后处理

        1. 提取时间事件 (DOME)
        2. 更新角色状态 (SCORE)
        3. 提取事实 (Phase 3)
        4. 更新套路统计 (CoKe)
        5. 分析角色心智 (ToM)
        6. 更新伏笔状态 (CFPG)
        """
        # 1. 初始化状态（如果需要）
        if not self.state_tracker.get_world_state(project_id):
            self.state_tracker.init_world_state(project_id, chapter_id)

        # 2. 更新套路使用 (CoKe)
        tropes = self.trope_tracker.extract_tropes_from_chapter(chapter_content)
        self.trope_tracker.record_trope_usage(project_id, chapter_id, tropes)

        # 注意：以下步骤实际需要LLM调用
        # 这里提供框架，具体由调用方实现

        # 3. 提取时间事件 (DOME) - 需要LLM分析
        # events = self.timeline.extract_events_from_chapter(chapter_id)
        # for event in events:
        #     self.timeline.add_event(...)

        # 4. 更新角色状态 (SCORE) - 需要LLM分析
        # for char_state_update in llm_analyze(chapter_content):
        #     self.state_tracker.update_character_state(...)

        # 5. 提取事实并检测矛盾 (Phase 3) - 需要LLM分析
        # facts = self.fact_extractor.extract_facts_from_chapter(chapter_id)
        # for fact in facts:
        #     self.fact_extractor.add_fact(...)

        # 6. 分析角色心智 (ToM) - 需要LLM分析
        # minds = self.mind_theory.analyze_character_mind(...)
        # for mind_update in minds:
        #     self.mind_theory.update_mind_from_llm(...)

        pass

    def process_llm_analysis_results(
        self,
        project_id: str,
        chapter_id: str,
        analysis_results: dict
    ):
        """
        处理LLM分析结果

        analysis_results: {
            "timeline_events": [...],
            "character_states": {...},
            "facts": [...],
            "character_minds": {...},
            "trope_usage": [...]
        }
        """
        # 处理时间事件
        for event_data in analysis_results.get("timeline_events", []):
            self.timeline.add_event(
                project_id=project_id,
                chapter_id=chapter_id,
                **event_data
            )

        # 处理角色状态
        for char_id, state_data in analysis_results.get("character_states", {}).items():
            self.state_tracker.update_character_state(
                character_id=char_id,
                chapter_id=chapter_id,
                **state_data
            )

        # 处理事实
        for fact_data in analysis_results.get("facts", []):
            self.fact_extractor.add_fact(
                project_id=project_id,
                chapter_id=chapter_id,
                **fact_data
            )

        # 处理套路
        tropes = analysis_results.get("trope_usage", [])
        if tropes:
            self.trope_tracker.record_trope_usage(project_id, chapter_id, tropes)

        # 处理心智状态
        for char_id, mind_data in analysis_results.get("character_minds", {}).items():
            self.mind_theory.update_mind_from_llm(
                character_id=char_id,
                chapter_id=chapter_id,
                mind_data=mind_data
            )

    # ============================================================
    # 查询接口
    # ============================================================

    def get_project_summary(self, project_id: str) -> dict:
        """获取项目一致性摘要"""
        return {
            "timeline": {
                "total_events": len(self.timeline.get_project_timeline(project_id))
            },
            "character_states": {
                "total": len(self.state_tracker.get_project_character_states(project_id)),
                "states": [
                    {"character_id": s.character_id, "status": s.status}
                    for s in self.state_tracker.get_project_character_states(project_id)
                ]
            },
            "consistency": self.consistency_checker.get_consistency_report(project_id),
            "foreshadow": self.foreshadow_manager.get_foreshadow_statistics(project_id),
            "trope": self.trope_tracker.get_trope_statistics(project_id)
        }

    def check_generation_quality(
        self,
        generated_content: str,
        project_id: str
    ) -> dict:
        """
        检查生成质量

        Returns:
            {
                "pass": bool,
                "issues": [...],
                "suggestions": [...]
            }
        """
        issues = []
        suggestions = []

        # 检查套路使用
        should_regen, trope_reason = self.trope_tracker.should_regenerate_for_trope(
            generated_content, project_id
        )
        if should_regen:
            issues.append({"type": "trope", "reason": trope_reason})

        # 检查SWAG锚点
        should_regen_swag, swag_reason = self.generation_controller.should_regenerate(
            generated_content
        )
        if should_regen_swag:
            issues.append({"type": "swag", "reason": swag_reason})
            for anchor in self.generation_controller.swag_must_include:
                if anchor not in generated_content:
                    suggestions.append(
                        self.generation_controller.get_regeneration_suggestion(anchor)
                    )

        return {
            "pass": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions
        }

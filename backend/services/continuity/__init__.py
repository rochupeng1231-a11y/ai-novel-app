# -*- coding: utf-8 -*-
"""
Continuity 模块 - 章节衔接与一致性管理

包含:
- TimelineGraph: DOME 时间知识图谱
- StateTracker: SCORE 动态状态追踪
- FactExtractor: 分类引导提取 + 矛盾配对
- ConsistencyChecker: ConStory-Checker 情节一致性检验
- TropeTracker: CoKe 防套话
- MindTheory: ToM 心智理论
- ForeshadowManager: CFPG 伏笔三元组
- GenerationController: BVSR/SWAG 生成控制
- ContinuityEngine: 统一入口
- ChapterAnalyzer: LLM章节分析服务
"""
from .timeline_graph import TimelineGraph
from .state_tracker import StateTracker
from .fact_extractor import FactExtractor
from .consistency_checker import ConsistencyChecker
from .trope_tracker import TropeTracker
from .mind_theory import MindTheory, ForeshadowManager
from .generation_controller import GenerationController, ChapterPlanValidator
from .continuity_engine import ContinuityEngine
from .chapter_analyzer import ChapterAnalyzer, LLMWritingAdvisor

__all__ = [
    # 核心类
    "ContinuityEngine",
    # DOME
    "TimelineGraph",
    # SCORE
    "StateTracker",
    # Phase 3
    "FactExtractor",
    # Phase 4
    "ConsistencyChecker",
    # Phase 5
    "TropeTracker",
    # Phase 6
    "MindTheory",
    "ForeshadowManager",
    # Phase 7
    "GenerationController",
    "ChapterPlanValidator",
    # 分析服务
    "ChapterAnalyzer",
    "LLMWritingAdvisor",
]

"""
数据库模型 - 使用SQLAlchemy
"""
from sqlalchemy import create_engine, Column, String, Text, Integer, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ai_novel.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    novel_type = Column(String)  # 小说类型（都市言情/玄幻修仙/悬疑推理/科幻未来/武侠江湖/校园青春）
    core_elements = Column(Text)  # 核心元素（JSON数组，最多3个）
    outline = Column(Text)  # AI 生成的大纲
    target_word_count = Column(Integer, default=300000)
    writing_phase = Column(String, default="outline")  # outline, planning, writing, revision
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    chapters = relationship("Chapter", back_populates="project", cascade="all, delete-orphan")
    characters = relationship("Character", back_populates="project", cascade="all, delete-orphan")
    foreshadows = relationship("Foreshadow", back_populates="project", cascade="all, delete-orphan")


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"))
    number = Column(Integer, nullable=False)
    title = Column(String)
    content = Column(Text, default="")
    status = Column(String, default="draft")  # draft, writing, completed
    review_status = Column(String, default="pending")  # pending, approved, rejected, revised
    word_count = Column(Integer, default=0)
    tension_score = Column(Float, default=0.5)
    timeline_order = Column(Integer, default=0)  # 时间线顺序
    synopsis = Column(Text, default="")  # 章节简介
    key_events = Column(Text, default="")  # 关键事件 JSON 数组
    char_statuses = Column(Text, default="")  # 角色状态快照 JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="chapters")
    versions = relationship("ChapterVersion", back_populates="chapter", cascade="all, delete-orphan")
    foreshadows = relationship("Foreshadow", back_populates="chapter")
    summary = relationship("ChapterSummary", back_populates="chapter", uselist=False, cascade="all, delete-orphan")
    dependencies_from = relationship("ChapterDependency", foreign_keys="ChapterDependency.chapter_id", back_populates="chapter")
    dependencies_to = relationship("ChapterDependency", foreign_keys="ChapterDependency.depends_on_id", back_populates="depends_on_chapter")


class ChapterSummary(Base):
    """章节摘要 - 用于后续章节写作时的上下文参考"""
    __tablename__ = "chapter_summaries"

    id = Column(String, primary_key=True)
    chapter_id = Column(String, ForeignKey("chapters.id", ondelete="CASCADE"), unique=True)
    content_summary = Column(Text, default="")  # 内容摘要 ~300字
    plot_progression = Column(Text, default="")  # 情节推进
    character_arcs = Column(Text, default="")  # 角色弧线变化
    foreshadows_triggered = Column(Text, default="")  # 触发的伏笔
    word_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    chapter = relationship("Chapter", back_populates="summary")


class ChapterDependency(Base):
    """章节依赖关系 - 支持顺序依赖和引用依赖"""
    __tablename__ = "chapter_dependencies"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"))
    chapter_id = Column(String, ForeignKey("chapters.id", ondelete="CASCADE"))
    depends_on_id = Column(String, ForeignKey("chapters.id", ondelete="CASCADE"))
    dependency_type = Column(String, default="sequential")  # sequential, reference, contrast
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    chapter = relationship("Chapter", foreign_keys=[chapter_id], back_populates="dependencies_from")
    depends_on_chapter = relationship("Chapter", foreign_keys=[depends_on_id], back_populates="dependencies_to")


class ChapterVersion(Base):
    __tablename__ = "chapter_versions"
    
    id = Column(String, primary_key=True)
    chapter_id = Column(String, ForeignKey("chapters.id", ondelete="CASCADE"))
    content = Column(Text)
    version_number = Column(Integer, nullable=False)
    change_summary = Column(String, default="")  # 变更摘要
    created_at = Column(DateTime, default=datetime.utcnow)
    
    chapter = relationship("Chapter", back_populates="versions")


class Character(Base):
    __tablename__ = "characters"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"))
    name = Column(String, nullable=False)
    alias = Column(String)
    personality = Column(Text)
    speech_style = Column(Text)
    forbidden_topics = Column(Text, default="[]")  # JSON数组
    avatar_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    project = relationship("Project", back_populates="characters")
    relations_from = relationship("CharacterRelation", foreign_keys="CharacterRelation.character_a_id", back_populates="character_a")
    relations_to = relationship("CharacterRelation", foreign_keys="CharacterRelation.character_b_id", back_populates="character_b")


class CharacterRelation(Base):
    __tablename__ = "character_relations"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"))
    character_a_id = Column(String, ForeignKey("characters.id", ondelete="CASCADE"))
    character_b_id = Column(String, ForeignKey("characters.id", ondelete="CASCADE"))
    relation_type = Column(String)  # 朋友、敌人、爱人、师徒等
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    character_a = relationship("Character", foreign_keys=[character_a_id], back_populates="relations_from")
    character_b = relationship("Character", foreign_keys=[character_b_id], back_populates="relations_to")


class Foreshadow(Base):
    __tablename__ = "foreshadows"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"))
    chapter_id = Column(String, ForeignKey("chapters.id", ondelete="SET NULL"))
    keyword = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default="planted")  # planted, triggered, resolved
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    
    project = relationship("Project", back_populates="foreshadows")
    chapter = relationship("Chapter", back_populates="foreshadows")


class ProjectDependency(Base):
    """项目依赖关系 - 用于多维度回退"""
    __tablename__ = "project_dependencies"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"))
    source_type = Column(String)  # chapter, character, relation, foreshadow
    source_id = Column(String)
    target_type = Column(String)
    target_id = Column(String)
    dependency_type = Column(String)  # references, triggers, contradicts
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================
# DOME 时间知识图谱 - Phase 1
# ============================================================
class TimelineEvent(Base):
    """时间线事件 - 追踪小说中的事件序列"""
    __tablename__ = "timeline_events"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"))
    chapter_id = Column(String, ForeignKey("chapters.id", ondelete="CASCADE"))
    event_type = Column(String)  # action/dialogue/state_change/foreshadow_plant/trigger/resolution
    event_time = Column(String)  # 故事内时间（如"第3天早晨"）
    sequence_order = Column(Integer, default=0)  # 在章节内的顺序
    content = Column(Text)  # 事件描述
    characters_involved = Column(Text, default="[]")  # JSON数组，涉及的角色ID列表
    cause_event_id = Column(String)  # 原因事件ID（因果链）
    effect_event_ids = Column(Text, default="[]")  # 结果事件ID列表（因果链）
    location = Column(String)  # 事件发生地点
    importance = Column(String, default="normal")  # high/normal/low
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================
# SCORE 动态状态追踪 + 统一真相源 - Phase 2
# ============================================================
class CharacterState(Base):
    """角色实时状态 - 追踪角色当前的位置、情绪、目标等"""
    __tablename__ = "character_states"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"))
    character_id = Column(String, ForeignKey("characters.id", ondelete="CASCADE"))
    chapter_id = Column(String)  # 记录该状态对应到哪一章结束时

    # 核心状态
    location = Column(String, default="")  # 当前位置
    emotion = Column(String, default="")  # 情绪状态
    physical_state = Column(String, default="")  # 身体状态（健康/受伤/疲劳等）
    goal = Column(String, default="")  # 当前目标
    status = Column(String, default="active")  # active/hidden/dead/absent

    # 关系状态 - JSON: {character_id: relation_type, ...}
    relationship_states = Column(Text, default="{}")

    # 物品清单 - JSON: [item1, item2, ...]
    inventory = Column(Text, default="[]")

    # 知识状态 - JSON: [knowledge1, knowledge2, ...]
    # 角色知道的信息
    knowledge = Column(Text, default="[]")

    # 秘密/隐藏信息 - JSON: [secret1, secret2, ...]
    # 角色知道但其他人不知道的
    secrets = Column(Text, default="[]")

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    character = relationship("Character", foreign_keys=[character_id])


class WorldState(Base):
    """世界状态 - 追踪故事世界的当前状态"""
    __tablename__ = "world_states"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), unique=True)
    chapter_id = Column(String)  # 当前章节

    # 世界状态
    current_arc = Column(String, default="")  # 当前故事弧
    main_conflict = Column(String, default="")  # 主要冲突
    timeline_progress = Column(String, default="")  # 时间线进度（如"第3天/共7天"）

    # 世界规则 - JSON: {rule: description, ...}
    world_rules = Column(Text, default="{}")

    # 重要地点 - JSON: {location: description, ...}
    locations = Column(Text, default="{}")

    # 势力/阵营 - JSON: {faction: status, ...}
    factions = Column(Text, default="{}")

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================
# 分类引导提取 + 矛盾配对 + 证据链 - Phase 3
# ============================================================
class ExtractedFact(Base):
    """提取的事实 - 用于一致性检验"""
    __tablename__ = "extracted_facts"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"))
    chapter_id = Column(String, ForeignKey("chapters.id", ondelete="CASCADE"))

    # 分类
    category = Column(String)  # character_action/dialogue/world_event/setting/emotion

    # 主语
    subject = Column(String)  # 主语（角色/物体/地点）

    # 谓语/事实
    predicate = Column(Text)  # 做什么/是什么/怎么样

    # 证据
    evidence_chapter = Column(String)  # 证据来源章节
    evidence_text = Column(Text)  # 原文摘录

    # 事实哈希 - 用于检测矛盾
    # 格式: category:subject:predicate_key
    # 例如: emotion:林逸尘:情绪=愤怒
    fact_hash = Column(String, index=True)

    # 置信度
    confidence = Column(String, default="high")  # high/medium/low

    created_at = Column(DateTime, default=datetime.utcnow)


class Contradiction(Base):
    """矛盾记录 - 检测到的事实矛盾"""
    __tablename__ = "contradictions"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"))

    # 矛盾的事实对
    fact_a_id = Column(String)  # 事实A的ID
    fact_b_id = Column(String)  # 事实B的ID

    # 矛盾内容
    fact_a_content = Column(Text)  # 事实A内容
    fact_b_content = Column(Text)  # 事实B内容

    # 矛盾类型
    contradiction_type = Column(String)  # character_contradiction/world_contradiction/timeline_contradiction

    # 严重程度
    severity = Column(String, default="medium")  # high/medium/low

    # 状态
    status = Column(String, default="detected")  # detected/confirmed/resolved/ignored

    # 解决方式
    resolution = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)


def init_db():
    """初始化数据库"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

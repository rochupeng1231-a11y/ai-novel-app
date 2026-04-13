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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    project = relationship("Project", back_populates="chapters")
    versions = relationship("ChapterVersion", back_populates="chapter", cascade="all, delete-orphan")
    foreshadows = relationship("Foreshadow", back_populates="chapter")


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

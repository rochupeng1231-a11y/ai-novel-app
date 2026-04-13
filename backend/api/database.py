"""
数据库 API - 项目、章节 CRUD
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
import json

from database.models import init_db, get_db, Project, Chapter, Character, CharacterRelation, Foreshadow, ChapterVersion

router = APIRouter(prefix="/api/db", tags=["数据库"])

# 启动时初始化数据库
init_db()


# ============ 项目 ============

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    target_word_count: int = 300000


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    target_word_count: int
    created_at: datetime
    updated_at: datetime


@router.post("/projects", response_model=ProjectResponse)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    db_project = Project(
        id=str(uuid.uuid4()),
        name=project.name,
        description=project.description,
        target_word_count=project.target_word_count
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@router.get("/projects", response_model=List[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.updated_at.desc()).all()


@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@router.delete("/projects/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    db.delete(project)
    db.commit()
    return {"message": "项目已删除"}


# ============ 章节 ============

class ChapterCreate(BaseModel):
    project_id: str
    number: int
    title: Optional[str] = ""


class ChapterUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None


class ChapterResponse(BaseModel):
    id: str
    project_id: str
    number: int
    title: Optional[str]
    content: Optional[str]
    status: str
    word_count: int
    tension_score: float
    created_at: datetime
    updated_at: datetime


@router.post("/chapters", response_model=ChapterResponse)
def create_chapter(chapter: ChapterCreate, db: Session = Depends(get_db)):
    db_chapter = Chapter(
        id=str(uuid.uuid4()),
        project_id=chapter.project_id,
        number=chapter.number,
        title=chapter.title
    )
    db.add(db_chapter)
    db.commit()
    db.refresh(db_chapter)
    return db_chapter


@router.get("/chapters/project/{project_id}", response_model=List[ChapterResponse])
def list_chapters(project_id: str, db: Session = Depends(get_db)):
    return db.query(Chapter).filter(Chapter.project_id == project_id).order_by(Chapter.number).all()


@router.get("/chapters/{chapter_id}", response_model=ChapterResponse)
def get_chapter(chapter_id: str, db: Session = Depends(get_db)):
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    return chapter


@router.put("/chapters/{chapter_id}", response_model=ChapterResponse)
def update_chapter(chapter_id: str, update: ChapterUpdate, db: Session = Depends(get_db)):
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    if update.title is not None:
        chapter.title = update.title
    if update.content is not None:
        chapter.content = update.content
        chapter.word_count = len(update.content.replace(" ", ""))
    if update.status is not None:
        chapter.status = update.status
    
    chapter.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(chapter)
    return chapter


@router.delete("/chapters/{chapter_id}")
def delete_chapter(chapter_id: str, db: Session = Depends(get_db)):
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    db.delete(chapter)
    db.commit()
    return {"message": "章节已删除"}


# ============ 章节版本 ============

class SaveVersionRequest(BaseModel):
    chapter_id: str
    content: str
    change_summary: str = ""


@router.post("/chapters/{chapter_id}/versions")
def save_version(chapter_id: str, request: SaveVersionRequest, db: Session = Depends(get_db)):
    """保存章节版本快照"""
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    
    # 获取最新版本号
    latest = db.query(ChapterVersion).filter(
        ChapterVersion.chapter_id == chapter_id
    ).order_by(ChapterVersion.version_number.desc()).first()
    
    new_version_number = (latest.version_number + 1) if latest else 1
    
    version = ChapterVersion(
        id=str(uuid.uuid4()),
        chapter_id=chapter_id,
        content=request.content,
        version_number=new_version_number,
        change_summary=request.change_summary
    )
    db.add(version)
    
    # 更新章节内容
    chapter.content = request.content
    chapter.word_count = len(request.content.replace(" ", ""))
    chapter.updated_at = datetime.utcnow()
    
    db.commit()
    return {"version_number": new_version_number, "version_id": version.id}


@router.get("/chapters/{chapter_id}/versions")
def list_versions(chapter_id: str, db: Session = Depends(get_db)):
    """获取章节所有版本"""
    versions = db.query(ChapterVersion).filter(
        ChapterVersion.chapter_id == chapter_id
    ).order_by(ChapterVersion.version_number.desc()).all()
    
    return [
        {
            "id": v.id,
            "version_number": v.version_number,
            "change_summary": v.change_summary,
            "created_at": v.created_at.isoformat() if v.created_at else None
        }
        for v in versions
    ]


@router.get("/chapters/{chapter_id}/versions/{version_number}")
def get_version(chapter_id: str, version_number: int, db: Session = Depends(get_db)):
    """获取指定版本内容"""
    version = db.query(ChapterVersion).filter(
        ChapterVersion.chapter_id == chapter_id,
        ChapterVersion.version_number == version_number
    ).first()
    
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")
    
    return {
        "id": version.id,
        "version_number": version.version_number,
        "content": version.content,
        "change_summary": version.change_summary,
        "created_at": version.created_at.isoformat() if version.created_at else None
    }


@router.post("/chapters/{chapter_id}/rollback/{version_number}")
def rollback_chapter(chapter_id: str, version_number: int, db: Session = Depends(get_db)):
    """回滚到指定版本"""
    version = db.query(ChapterVersion).filter(
        ChapterVersion.chapter_id == chapter_id,
        ChapterVersion.version_number == version_number
    ).first()
    
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")
    
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if chapter:
        chapter.content = version.content
        chapter.word_count = len(version.content.replace(" ", ""))
        chapter.updated_at = datetime.utcnow()
        db.commit()
    
    return {"message": "回滚成功", "restored_version": version_number}


# ============ 角色 ============

class CharacterCreate(BaseModel):
    project_id: str
    name: str
    alias: Optional[str] = ""
    personality: Optional[str] = ""
    speech_style: Optional[str] = ""
    forbidden_topics: List[str] = []


class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    alias: Optional[str] = None
    personality: Optional[str] = None
    speech_style: Optional[str] = None
    forbidden_topics: Optional[List[str]] = None


class CharacterResponse(BaseModel):
    id: str
    project_id: str
    name: str
    alias: Optional[str]
    personality: Optional[str]
    speech_style: Optional[str]
    forbidden_topics: List[str]
    created_at: datetime


@router.post("/characters", response_model=CharacterResponse)
def create_character(character: CharacterCreate, db: Session = Depends(get_db)):
    db_char = Character(
        id=str(uuid.uuid4()),
        project_id=character.project_id,
        name=character.name,
        alias=character.alias,
        personality=character.personality,
        speech_style=character.speech_style,
        forbidden_topics=json.dumps(character.forbidden_topics)
    )
    db.add(db_char)
    db.commit()
    db.refresh(db_char)
    return {**db_char.__dict__, "forbidden_topics": json.loads(db_char.forbidden_topics or "[]")}


@router.get("/characters/project/{project_id}", response_model=List[CharacterResponse])
def list_characters(project_id: str, db: Session = Depends(get_db)):
    characters = db.query(Character).filter(Character.project_id == project_id).all()
    return [
        {**c.__dict__, "forbidden_topics": json.loads(c.forbidden_topics or "[]")}
        for c in characters
    ]


@router.put("/characters/{character_id}", response_model=CharacterResponse)
def update_character(character_id: str, update: CharacterUpdate, db: Session = Depends(get_db)):
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    if update.name is not None:
        character.name = update.name
    if update.alias is not None:
        character.alias = update.alias
    if update.personality is not None:
        character.personality = update.personality
    if update.speech_style is not None:
        character.speech_style = update.speech_style
    if update.forbidden_topics is not None:
        character.forbidden_topics = json.dumps(update.forbidden_topics)
    
    character.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(character)
    return {**character.__dict__, "forbidden_topics": json.loads(character.forbidden_topics or "[]")}


@router.delete("/characters/{character_id}")
def delete_character(character_id: str, db: Session = Depends(get_db)):
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    db.delete(character)
    db.commit()
    return {"message": "角色已删除"}


# ============ 角色关系 ============

class RelationCreate(BaseModel):
    project_id: str
    character_a_id: str
    character_b_id: str
    relation_type: str
    description: str = ""


class RelationResponse(BaseModel):
    id: str
    project_id: str
    character_a_id: str
    character_b_id: str
    relation_type: str
    description: Optional[str]


@router.post("/relations", response_model=RelationResponse)
def create_relation(relation: RelationCreate, db: Session = Depends(get_db)):
    db_rel = CharacterRelation(
        id=str(uuid.uuid4()),
        project_id=relation.project_id,
        character_a_id=relation.character_a_id,
        character_b_id=relation.character_b_id,
        relation_type=relation.relation_type,
        description=relation.description
    )
    db.add(db_rel)
    db.commit()
    db.refresh(db_rel)
    return db_rel


@router.get("/relations/project/{project_id}")
def list_relations(project_id: str, db: Session = Depends(get_db)):
    relations = db.query(CharacterRelation).filter(CharacterRelation.project_id == project_id).all()
    return [
        {
            "id": r.id,
            "character_a_id": r.character_a_id,
            "character_b_id": r.character_b_id,
            "relation_type": r.relation_type,
            "description": r.description
        }
        for r in relations
    ]


# ============ 伏笔 ============

class ForeshadowCreate(BaseModel):
    project_id: str
    chapter_id: Optional[str]
    keyword: str
    description: str = ""
    status: str = "planted"


class ForeshadowUpdate(BaseModel):
    keyword: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


@router.post("/foreshadows", response_model=List[dict])
def create_foreshadow(fs: ForeshadowCreate, db: Session = Depends(get_db)):
    db_fs = Foreshadow(
        id=str(uuid.uuid4()),
        project_id=fs.project_id,
        chapter_id=fs.chapter_id,
        keyword=fs.keyword,
        description=fs.description,
        status=fs.status
    )
    db.add(db_fs)
    db.commit()
    db.refresh(db_fs)
    return db_fs


@router.get("/foreshadows/project/{project_id}")
def list_foreshadows(project_id: str, db: Session = Depends(get_db)):
    foreshadows = db.query(Foreshadow).filter(Foreshadow.project_id == project_id).all()
    return [
        {
            "id": f.id,
            "chapter_id": f.chapter_id,
            "keyword": f.keyword,
            "description": f.description,
            "status": f.status,
            "created_at": f.created_at.isoformat() if f.created_at else None,
            "resolved_at": f.resolved_at.isoformat() if f.resolved_at else None
        }
        for f in foreshadows
    ]


@router.put("/foreshadows/{foreshadow_id}")
def update_foreshadow(foreshadow_id: str, update: ForeshadowUpdate, db: Session = Depends(get_db)):
    fs = db.query(Foreshadow).filter(Foreshadow.id == foreshadow_id).first()
    if not fs:
        raise HTTPException(status_code=404, detail="伏笔不存在")
    
    if update.keyword is not None:
        fs.keyword = update.keyword
    if update.description is not None:
        fs.description = update.description
    if update.status is not None:
        fs.status = update.status
        if update.status == "resolved":
            fs.resolved_at = datetime.utcnow()
    
    db.commit()
    return {"message": "伏笔已更新"}

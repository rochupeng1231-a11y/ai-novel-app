# -*- coding: utf-8 -*-
"""
SCORE 动态状态追踪服务

追踪角色和世界的实时状态，作为写作的统一真相源
"""
import uuid
import json
from datetime import datetime
from sqlalchemy.orm import Session
from database.models import CharacterState, WorldState, Character, Project, Chapter


class StateTracker:
    """状态追踪管理器 - 统一真相源"""

    def __init__(self, db: Session):
        self.db = db

    # ============================================================
    # 角色状态管理
    # ============================================================

    def init_character_states(self, project_id: str):
        """初始化项目的所有角色状态"""
        characters = self.db.query(Character).filter(
            Character.project_id == project_id
        ).all()

        states = []
        for char in characters:
            # 检查是否已存在
            existing = self.db.query(CharacterState).filter(
                CharacterState.character_id == char.id
            ).first()
            if existing:
                continue

            state = CharacterState(
                id=str(uuid.uuid4()),
                project_id=project_id,
                character_id=char.id,
                status="active",
                relationship_states="{}",
                inventory="[]",
                knowledge="[]",
                secrets="[]"
            )
            self.db.add(state)
            states.append(state)

        self.db.commit()
        return states

    def get_character_state(self, character_id: str) -> CharacterState:
        """获取角色的最新状态"""
        return self.db.query(CharacterState).filter(
            CharacterState.character_id == character_id
        ).order_by(CharacterState.updated_at.desc()).first()

    def get_project_character_states(self, project_id: str) -> list[CharacterState]:
        """获取项目的所有角色状态"""
        return self.db.query(CharacterState).filter(
            CharacterState.project_id == project_id
        ).all()

    def update_character_state(
        self,
        character_id: str,
        chapter_id: str,
        **kwargs
    ) -> CharacterState:
        """更新角色状态"""
        state = self.get_character_state(character_id)

        if not state:
            # 如果不存在，创建新的
            char = self.db.query(Character).filter(Character.id == character_id).first()
            if not char:
                return None
            state = CharacterState(
                id=str(uuid.uuid4()),
                project_id=char.project_id,
                character_id=character_id,
                status="active",
                relationship_states="{}",
                inventory="[]",
                knowledge="[]",
                secrets="[]"
            )
            self.db.add(state)

        # 更新字段
        for key, value in kwargs.items():
            if hasattr(state, key):
                if key in ["relationship_states", "inventory", "knowledge", "secrets"]:
                    # 这些字段存JSON
                    if isinstance(value, list):
                        value = json.dumps(value, ensure_ascii=False)
                    elif not isinstance(value, str):
                        value = json.dumps(value, ensure_ascii=False)
                setattr(state, key, value)

        state.chapter_id = chapter_id
        state.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(state)
        return state

    def add_knowledge(self, character_id: str, knowledge_item: str):
        """角色获得新知识"""
        state = self.get_character_state(character_id)
        if state:
            knowledge_list = json.loads(state.knowledge or "[]")
            if knowledge_item not in knowledge_list:
                knowledge_list.append(knowledge_item)
                state.knowledge = json.dumps(knowledge_list, ensure_ascii=False)
                state.updated_at = datetime.utcnow()
                self.db.commit()

    def add_inventory_item(self, character_id: str, item: str):
        """角色获得物品"""
        state = self.get_character_state(character_id)
        if state:
            inventory_list = json.loads(state.inventory or "[]")
            if item not in inventory_list:
                inventory_list.append(item)
                state.inventory = json.dumps(inventory_list, ensure_ascii=False)
                state.updated_at = datetime.utcnow()
                self.db.commit()

    def remove_inventory_item(self, character_id: str, item: str):
        """角色失去物品"""
        state = self.get_character_state(character_id)
        if state:
            inventory_list = json.loads(state.inventory or "[]")
            if item in inventory_list:
                inventory_list.remove(item)
                state.inventory = json.dumps(inventory_list, ensure_ascii=False)
                state.updated_at = datetime.utcnow()
                self.db.commit()

    def update_relationship(
        self,
        character_id: str,
        target_id: str,
        relation_type: str
    ):
        """更新角色关系"""
        state = self.get_character_state(character_id)
        if state:
            relations = json.loads(state.relationship_states or "{}")
            relations[target_id] = relation_type
            state.relationship_states = json.dumps(relations, ensure_ascii=False)
            state.updated_at = datetime.utcnow()
            self.db.commit()

    def get_character_relationships(self, character_id: str) -> dict:
        """获取角色与其他角色的关系"""
        state = self.get_character_state(character_id)
        if state:
            return json.loads(state.relationship_states or "{}")
        return {}

    # ============================================================
    # 世界状态管理
    # ============================================================

    def get_world_state(self, project_id: str) -> WorldState:
        """获取世界状态"""
        return self.db.query(WorldState).filter(
            WorldState.project_id == project_id
        ).first()

    def init_world_state(self, project_id: str, chapter_id: str = None) -> WorldState:
        """初始化世界状态"""
        existing = self.get_world_state(project_id)
        if existing:
            return existing

        world = WorldState(
            id=str(uuid.uuid4()),
            project_id=project_id,
            chapter_id=chapter_id,
            world_rules="{}",
            locations="{}",
            factions="{}"
        )
        self.db.add(world)
        self.db.commit()
        self.db.refresh(world)
        return world

    def update_world_state(
        self,
        project_id: str,
        chapter_id: str = None,
        **kwargs
    ) -> WorldState:
        """更新世界状态"""
        world = self.get_world_state(project_id)

        if not world:
            world = self.init_world_state(project_id, chapter_id)

        for key, value in kwargs.items():
            if hasattr(world, key):
                if key in ["world_rules", "locations", "factions"]:
                    if isinstance(value, dict):
                        value = json.dumps(value, ensure_ascii=False)
                    elif not isinstance(value, str):
                        value = json.dumps(value, ensure_ascii=False)
                setattr(world, key, value)

        if chapter_id:
            world.chapter_id = chapter_id
        world.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(world)
        return world

    # ============================================================
    # 统一真相源 - 获取写作上下文
    # ============================================================

    def get_writing_context(self, project_id: str, chapter_id: str = None) -> dict:
        """
        获取写作所需的完整上下文
        这是向AI传递信息的唯一入口
        """
        context = {
            "characters": [],
            "world": None,
            "important_events": []
        }

        # 获取角色状态
        char_states = self.get_project_character_states(project_id)
        for state in char_states:
            char = self.db.query(Character).filter(Character.id == state.character_id).first()
            if char:
                context["characters"].append({
                    "id": char.id,
                    "name": char.name,
                    "status": state.status,
                    "location": state.location,
                    "emotion": state.emotion,
                    "physical_state": state.physical_state,
                    "goal": state.goal,
                    "relationships": json.loads(state.relationship_states or "{}"),
                    "inventory": json.loads(state.inventory or "[]"),
                    "knowledge": json.loads(state.knowledge or "[]"),
                    "secrets": json.loads(state.secrets or "[]")
                })

        # 获取世界状态
        world = self.get_world_state(project_id)
        if world:
            context["world"] = {
                "current_arc": world.current_arc,
                "main_conflict": world.main_conflict,
                "timeline_progress": world.timeline_progress,
                "world_rules": json.loads(world.world_rules or "{}"),
                "locations": json.loads(world.locations or "{}"),
                "factions": json.loads(world.factions or "{}")
            }

        return context

    def format_context_for_prompt(self, project_id: str, chapter_id: str = None) -> str:
        """
        将上下文格式化为prompt字符串
        """
        ctx = self.get_writing_context(project_id, chapter_id)
        parts = []

        # 角色状态
        if ctx["characters"]:
            parts.append("【角色状态】")
            for char in ctx["characters"]:
                parts.append(f"- {char['name']}: {char['status']}")
                if char['location']:
                    parts.append(f"  位置: {char['location']}")
                if char['emotion']:
                    parts.append(f"  情绪: {char['emotion']}")
                if char['physical_state']:
                    parts.append(f"  状态: {char['physical_state']}")
                if char['goal']:
                    parts.append(f"  目标: {char['goal']}")
                if char['inventory']:
                    parts.append(f"  物品: {', '.join(char['inventory'])}")
                if char['knowledge']:
                    parts.append(f"  已知: {', '.join(char['knowledge'][:3])}")

        # 世界状态
        if ctx["world"]:
            world = ctx["world"]
            parts.append("\n【世界状态】")
            if world["current_arc"]:
                parts.append(f"当前故事弧: {world['current_arc']}")
            if world["main_conflict"]:
                parts.append(f"主要冲突: {world['main_conflict']}")
            if world["timeline_progress"]:
                parts.append(f"时间进度: {world['timeline_progress']}")

        return "\n".join(parts)

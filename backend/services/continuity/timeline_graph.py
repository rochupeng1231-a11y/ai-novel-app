# -*- coding: utf-8 -*-
"""
DOME 时间知识图谱服务

追踪小说中的事件序列、时间线、因果关系
"""
import uuid
import json
from datetime import datetime
from sqlalchemy.orm import Session
from database.models import TimelineEvent, Chapter, Character


class TimelineGraph:
    """时间知识图谱管理器"""

    def __init__(self, db: Session):
        self.db = db

    def extract_events_from_chapter(self, chapter_id: str) -> list[dict]:
        """
        从章节内容中提取时间事件
        实际调用LLM进行提取，这里先定义提取的事件结构
        """
        chapter = self.db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if not chapter:
            return []

        # 这里返回提取的事件列表结构
        # 实际由LLM填充具体事件
        return []

    def add_event(
        self,
        project_id: str,
        chapter_id: str,
        event_type: str,
        content: str,
        event_time: str = None,
        characters_involved: list = None,
        cause_event_id: str = None,
        location: str = None,
        importance: str = "normal"
    ) -> TimelineEvent:
        """添加一个事件到时间线"""
        # 获取当前章节的最后一个事件顺序
        last_event = self.db.query(TimelineEvent).filter(
            TimelineEvent.chapter_id == chapter_id
        ).order_by(TimelineEvent.sequence_order.desc()).first()

        next_order = (last_event.sequence_order + 1) if last_event else 1

        event = TimelineEvent(
            id=str(uuid.uuid4()),
            project_id=project_id,
            chapter_id=chapter_id,
            event_type=event_type,
            event_time=event_time,
            sequence_order=next_order,
            content=content,
            characters_involved=json.dumps(characters_involved or [], ensure_ascii=False),
            cause_event_id=cause_event_id,
            location=location,
            importance=importance,
            effect_event_ids="[]",
            created_at=datetime.utcnow()
        )

        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def link_events(self, event_id: str, cause_event_id: str):
        """建立因果关系链接"""
        event = self.db.query(TimelineEvent).filter(TimelineEvent.id == event_id).first()
        if event:
            event.cause_event_id = cause_event_id
            self.db.commit()

    def add_effect(self, event_id: str, effect_event_id: str):
        """添加结果事件"""
        event = self.db.query(TimelineEvent).filter(TimelineEvent.id == event_id).first()
        if event:
            effects = json.loads(event.effect_event_ids or "[]")
            if effect_event_id not in effects:
                effects.append(effect_event_id)
                event.effect_event_ids = json.dumps(effects, ensure_ascii=False)
                self.db.commit()

    def get_chapter_events(self, chapter_id: str) -> list[TimelineEvent]:
        """获取某章节的所有事件（按顺序）"""
        return self.db.query(TimelineEvent).filter(
            TimelineEvent.chapter_id == chapter_id
        ).order_by(TimelineEvent.sequence_order).all()

    def get_project_timeline(self, project_id: str, limit: int = 50) -> list[TimelineEvent]:
        """
        获取项目的完整时间线
        按章节顺序排列
        """
        return self.db.query(TimelineEvent).filter(
            TimelineEvent.project_id == project_id
        ).join(
            Chapter, TimelineEvent.chapter_id == Chapter.id
        ).order_by(
            Chapter.number, TimelineEvent.sequence_order
        ).limit(limit).all()

    def get_character_events(
        self,
        project_id: str,
        character_id: str,
        limit: int = 20
    ) -> list[TimelineEvent]:
        """获取某角色的所有事件"""
        return self.db.query(TimelineEvent).filter(
            TimelineEvent.project_id == project_id,
            TimelineEvent.characters_involved.contains(character_id)
        ).join(
            Chapter, TimelineEvent.chapter_id == Chapter.id
        ).order_by(
            Chapter.number, TimelineEvent.sequence_order
        ).limit(limit).all()

    def get_events_before_chapter(
        self,
        project_id: str,
        before_chapter_id: str,
        limit: int = 10
    ) -> list[TimelineEvent]:
        """获取某章节之前的事件（用于衔接）"""
        chapter = self.db.query(Chapter).filter(Chapter.id == before_chapter_id).first()
        if not chapter:
            return []

        return self.db.query(TimelineEvent).filter(
            TimelineEvent.project_id == project_id,
            Chapter.number < chapter.number
        ).join(
            Chapter, TimelineEvent.chapter_id == Chapter.id
        ).order_by(
            Chapter.number.desc(), TimelineEvent.sequence_order.desc()
        ).limit(limit).all()

    def get_last_n_chapters_context(
        self,
        project_id: str,
        current_chapter_id: str,
        n: int = 1
    ) -> dict:
        """
        获取最近n章的事件上下文
        返回: {events: [...], summary: "...", prev_chapter_content: "..."}
        """
        chapter = self.db.query(Chapter).filter(
            Chapter.id == current_chapter_id
        ).first()
        if not chapter:
            return {"events": [], "summary": "", "prev_chapter_content": ""}

        # 获取之前n章
        prev_chapters = self.db.query(Chapter).filter(
            Chapter.project_id == project_id,
            Chapter.number < chapter.number
        ).order_by(Chapter.number.desc()).limit(n).all()

        if not prev_chapters:
            return {"events": [], "summary": "", "prev_chapter_content": ""}

        all_events = []
        prev_chapter_content = ""

        for ch in reversed(prev_chapters):  # 正序排列
            events = self.get_chapter_events(ch.id)
            all_events.extend(events)

            # 记录最后一章的实际内容（用于回退）
            if ch.number == prev_chapters[-1].number and ch.content:
                prev_chapter_content = ch.content

        # 生成摘要
        summary_parts = []
        for ch in prev_chapters:
            summary_parts.append(f"第{ch.number}章《{ch.title}》发生：")
            events = self.get_chapter_events(ch.id)
            for e in events:
                if e.importance == "high":
                    summary_parts.append(f"  - {e.content}")

        return {
            "events": all_events,
            "summary": "\n".join(summary_parts),
            "last_chapter_events": all_events[-5:] if all_events else [],
            "prev_chapter_content": prev_chapter_content  # 新增：实际章节内容
        }

    def get_event_chain(self, event_id: str, depth: int = 3) -> dict:
        """
        获取事件因果链
        返回事件及其原因/结果事件
        """
        event = self.db.query(TimelineEvent).filter(
            TimelineEvent.id == event_id
        ).first()
        if not event:
            return {}

        chain = {
            "event": event,
            "causes": [],
            "effects": []
        }

        # 获取原因事件
        if event.cause_event_id:
            cause = self.db.query(TimelineEvent).filter(
                TimelineEvent.id == event.cause_event_id
            ).first()
            if cause:
                chain["causes"].append(cause)

        # 获取结果事件
        if event.effect_event_ids:
            effect_ids = json.loads(event.effect_event_ids)
            for eff_id in effect_ids[:depth]:
                eff = self.db.query(TimelineEvent).filter(
                    TimelineEvent.id == eff_id
                ).first()
                if eff:
                    chain["effects"].append(eff)

        return chain

    def delete_chapter_events(self, chapter_id: str):
        """删除某章节的所有事件（章节删除时调用）"""
        self.db.query(TimelineEvent).filter(
            TimelineEvent.chapter_id == chapter_id
        ).delete()
        self.db.commit()

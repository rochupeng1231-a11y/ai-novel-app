# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working on this codebase.

## Critical Rules

### No Large Files
- **Backend Python files**: No single file may exceed **200 lines**
- **Frontend JS files**: No single file may exceed **200 lines**
- **If a file approaches 150 lines, proactively split it into modules**

### Modularization Required
- Each file should have a single, clear responsibility
- Related functionality should be extracted into separate modules
- Follow the existing patterns in this codebase

### Code Editing
- Favor simple, modular solutions; keep indentation ≤3 levels
- Functions should be single-purpose
- Reuse existing patterns; Tailwind/shadcn defaults for frontend
- Comments only when intent is non-obvious; keep them short
- Enforce accessibility, consistent spacing (multiples of 4), ≤2 accent colors

---

## Overview

AI 写小说 (AI Novel Writing) — a guided novel writing tool with AI generation, real-time tension analysis, continuity tracking, and batch writing with review workflow.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Vanilla HTML/CSS/JS (no framework, modular) |
| Backend | FastAPI + Pydantic + SQLAlchemy |
| AI | MiniMax API (primary), with Kimi/DeepSeek/Claude support |
| Database | SQLite (`ai_novel.db`) |
| Server | uvicorn on port 8000, HTTP server on port 3000 |

## Commands

```bash
# Start backend (development with auto-reload)
cd ai-novel-app && .venv/Scripts/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Start frontend (serves static files on port 3000)
cd ai-novel-app/frontend && .venv/Scripts/python -m http.server 3000
```

## Architecture

```
Frontend (Browser)
    │
    ├── HTTP → uvicorn (port 8000) → FastAPI
    │                        │
    │                        ├── /api/db/*           → database.py (CRUD)
    │                        ├── /api/writing/*      → writing.py (单章节写作)
    │                        ├── /api/writing/batch* → batch_writing.py (批量写作状态)
    │                        ├── /api/continuity/*   → continuity.py (连贯性API)
    │                        ├── /api/rollback/*    → rollback.py
    │                        └── /api/chapters/*, /api/characters/*
    │
    └── HTTP → port 3000 static files
```

## Backend API Structure

| File | Lines | Responsibility |
|------|-------|----------------|
| `api/writing.py` | ~180 | 单章节流式写作 |
| `api/batch_writing.py` | ~160 | 批量写作状态管理（复用单章API） |
| `api/continuity.py` | ~250 | 连贯性API端点 |
| `api/database.py` | ~400 | 数据库CRUD |
| `api/rollback.py` | ~200 | 回退API |

**API Design Rules**:
- If an API file exceeds 200 lines, split it
- Batch writing reuses single-chapter writing API; never duplicate logic
- Pydantic schemas in `backend/models/schemas.py`

## Continuity System (连贯性系统)

The continuity system ensures chapter coherence using multiple subsystems:

| Subsystem | File | Purpose |
|-----------|------|---------|
| DOME | `timeline_graph.py` | 时间知识图谱，事件追踪 |
| SCORE | `state_tracker.py` | 角色/世界状态追踪 |
| CoKe | `trope_tracker.py` | 防套话检测 |
| CFPG | `mind_theory.py` | 伏笔三元组管理 |
| ConStory | `consistency_checker.py` | 情节一致性检验 |
| BVSR/SWAG | `generation_controller.py` | 生成控制 |

**Key Principle**: All external information must flow through Continuity state tables, not raw chapter content.

## Frontend Modules

| Module | Max Lines | Responsibility |
|--------|-----------|----------------|
| `modules/state.js` | ~100 | Global state manager |
| `modules/api.js` | ~150 | HTTP requests, SSE handling |
| `modules/project.js` | ~150 | Project/chapter CRUD |
| `modules/outline.js` | ~200 | Outline generation |
| `modules/writing.js` | ~150 | Writing operations |
| `app.js` | ~200 | Orchestrator, UI wiring |

**Module rules**:
- Export via `window.<moduleName>`
- Access state via `stateManager.state`
- Call APIs via `api.*` functions
- `app.js` is the only file touching DOM directly
- **If any module approaches 150 lines, split it**

## Database Schema

Key tables: `projects`, `chapters`, `chapter_versions`, `characters`, `character_relations`, `foreshadows`.

Extended tables for continuity: `timeline_events`, `character_states`, `world_states`, `extracted_facts`, `contradictions`.

## Configuration

Environment variables in `.env`:
- `MINIMAX_API_KEY` — primary AI provider
- `KIMI_API_KEY`, `DEEPSEEK_API_KEY`, `CLAUDE_API_KEY` — alternatives
- `DATABASE_URL` — defaults to `sqlite:///./ai_novel.db`

## Known Issues

- Frontend modules must stay under 200 lines each
- Backend API files must stay under 200 lines each
- If editing causes a file to exceed these limits, refactor immediately
- No user authentication implemented

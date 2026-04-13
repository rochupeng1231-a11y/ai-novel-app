# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

AI 写小说 (AI Novel Writing) — a guided novel writing tool with AI generation, real-time tension analysis, and multi-dimensional rollback capabilities.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Vanilla HTML/CSS/JS (no framework, modular) |
| Backend | FastAPI + Pydantic + SQLAlchemy |
| AI | MiniMax API (primary), with Kimi/DeepSeek/Claude support via `AIAggregator` |
| Database | SQLite (`ai_novel.db`) |
| Server | uvicorn on port 8000, HTTP server on port 3000 for frontend |

## Commands

```bash
# Install dependencies
.venv/Scripts/pip install -r requirements.txt

# Start backend (development with auto-reload)
.venv/Scripts/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Start frontend (serves static files on port 3000)
cd frontend && .venv/Scripts/python -m http.server 3000

# Run tests
.venv/Scripts/python tests/run_tests.py

# Run a single test file
.venv/Scripts/python -m pytest tests/backend/api/test_chapters.py -v
```

## Architecture

```
Frontend (Browser)
    │
    ├── HTTP → uvicorn (port 8000) → FastAPI
    │                        │
    │                        ├── /api/db/*     → database.py (Projects, Chapters, Characters, Relations, Foreshadows CRUD)
    │                        ├── /api/writing/* → writing.py → WritingEngine → ai_aggregator (MiniMax/Kimi/DeepSeek/Claude)
    │                        ├── /api/chapters/* → chapters.py (chapter-specific routes)
    │                        ├── /api/characters/* → characters.py (character routes)
    │                        └── /api/rollback/* → rollback.py → RollbackEngine (multi-dimensional rollback)
    │
    └── HTTP → port 3000 static files (index.html, app.js, styles/)

Database (SQLite via SQLAlchemy ORM)
```

### Key Services

- **`WritingEngine`** (`backend/services/writing_engine.py`): Core writing orchestration. Routes `续写/润色/改写/概括` instructions through task-type-specific prompts to `ai_aggregator`. Integrates `TensionAnalyzer` for post-generation scoring.
- **`TensionAnalyzer`** (`backend/services/tension_analyzer.py`): Keyword-based tension analysis on four dimensions (conflict, suspense, emotion, rhythm), each 0.0–1.0. Weights equally for overall score. Used by `WritingEngine` after AI generation and by the frontend tension meter.
- **`AIAggregator`** (`backend/services/ai_client.py`): Unified AI client with strategy pattern — routes task types to different providers (`outline→deepseek`, `draft→kimi`, `core/polish→claude`). Single global instance `ai_aggregator`.
- **`RollbackEngine`** (`backend/services/rollback_engine.py`): Tracks `ProjectDependency` records to analyze and execute multi-dimensional rollbacks across chapters, characters, and foreshadows.
- **`VersionControl`** (`backend/services/version_control.py`): Optimistic locking via version numbers on chapters.

### API Design

All API routes follow REST patterns. Pydantic `BaseModel` for request/response validation. Database access via SQLAlchemy `Session` dependency injection (`get_db`).

Notable: `/api/writing/` returns a `WritingResponse` defined in `backend/models/schemas.py`, not inline.

### Frontend Modules

The frontend uses a modular JS architecture (no framework). All modules live in `frontend/modules/`:

| Module | Responsibility |
|--------|----------------|
| `modules/state.js` | Global `stateManager` — holds app state, provides setters |
| `modules/api.js` | All backend HTTP requests, including SSE streaming via `api.writeStream()` |
| `modules/project.js` | Project CRUD, chapter management, data loading |
| `modules/outline.js` | Novel type/element selection, outline generation, chapter auto-creation from outline |
| `modules/writing.js` | Writing operations (续写/润色/改写/概括), real-time tension analysis, word count |
| `app.js` | Thin orchestrator — wires modules, exposes `window.app`, calls `updateUI()` |

**Module load order** (in `index.html`): `state.js` → `api.js` → `project.js` → `outline.js` → `writing.js` → `app.js`

**Module rules**:
- Modules export via `window.<moduleName>` (e.g., `window.projectModule`, `window.outlineModule`)
- Modules access state via `stateManager.state` (from `state.js`)
- Modules call API via `api.*` functions (from `api.js`)
- `app.js` is the only file that knows about DOM elements and calls `updateUI()`
- UI components (`ChapterList`, `TensionMeter`, `RelationGraph`, `KnowledgeBase`) are class-based in `components/`
- **No file in `frontend/` may exceed ~200 lines. If a module grows beyond that, split it further.**
- The SSE streaming helper lives in `api.writeStream()` — all streaming requests go through there. Do not write inline SSE parsing in other modules.

### Database Schema

SQLite via SQLAlchemy `Base.metadata.create_all(bind=engine)` at import time in `database.py`. Schema can also be initialized from `database/schema.sql`.

Tables: `projects`, `chapters`, `chapter_versions`, `characters`, `character_relations`, `foreshadows`, `project_dependencies`.

## Configuration

Environment variables in `.env` (copy from `.env.example`):
- `MINIMAX_API_KEY` — primary AI provider
- `KIMI_API_KEY`, `DEEPSEEK_API_KEY`, `CLAUDE_API_KEY` — optional alternatives
- `DATABASE_URL` — defaults to `sqlite:///./ai_novel.db`

## Known Issues

- `frontend/app.js` is the canonical source; ensure it's not 0 bytes before running
- Tension analysis is keyword-based (rule-based), not ML-powered
- Rollback engine's `ProjectDependency` tracking requires manual population
- No user authentication

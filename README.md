# AI 写小说应用

> 集成 AI 生成、实时张力分析、多维度回退的小说写作工具

**服务地址**: http://localhost:3000 (开发环境)

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | 原生 HTML/CSS/JS（无框架，模块化） |
| 后端 | FastAPI + Pydantic + SQLAlchemy |
| AI | MiniMax API（`MiniMax-M2.7` 模型）+ Anthropic SDK |
| 数据库 | SQLite（`ai_novel.db`） |
| 服务器 | uvicorn (8000) + http.server (3000) |

---

## 项目结构

```
ai-novel-app/
├── frontend/                    # 前端资源
│   ├── index.html               # 入口页面
│   ├── app.js                   # 主应用逻辑（模块编排）
│   ├── modules/                 # 功能模块
│   │   ├── api.js              # API 客户端（含 SSE 流式处理）
│   │   ├── state.js            # 全局状态管理
│   │   ├── project.js          # 项目/章节 CRUD
│   │   ├── outline.js          # 大纲生成（5阶段增量）
│   │   └── writing.js          # 写作操作（续写/润色/改写/概括）
│   └── components/              # UI 组件
│       ├── ChapterList.js      # 章节列表
│       ├── TensionMeter.js     # 张力仪表盘
│       ├── RelationGraph.js    # 人物关系图谱
│       └── KnowledgeBase.js    # 知识库面板
│
├── backend/                     # 后端（uvicorn 端口 8000）
│   ├── main.py                  # FastAPI 入口、CORS 配置
│   ├── api/                     # API 路由层
│   │   ├── database.py         # 项目/章节/角色/伏笔 CRUD
│   │   ├── writing.py          # AI 流式写作路由
│   │   ├── chapters.py         # 章节操作路由
│   │   ├── characters.py       # 角色路由
│   │   └── rollback.py         # 多维度回退路由
│   ├── services/                # 业务逻辑层
│   │   ├── ai_client.py        # MiniMax Anthropic SDK 客户端
│   │   ├── writing_engine.py   # 写作引擎（Prompt 构造）
│   │   ├── tension_analyzer.py  # 实时张力分析
│   │   └── rollback_engine.py  # 多维度回退引擎
│   ├── models/
│   │   └── schemas.py          # Pydantic 数据模型
│   └── config.py               # 配置（API 密钥、超时等）
│
├── database/
│   ├── models.py               # SQLAlchemy 模型
│   └── schema.sql              # SQLite 表结构参考
│
└── requirements.txt             # Python 依赖
```

---

## 快速启动

```bash
# 安装依赖
.venv/Scripts/pip install -r requirements.txt

# 启动后端（开发模式）
.venv/Scripts/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# 启动前端（另一个终端）
cd frontend && .venv/Scripts/python -m http.server 3000

# 访问 http://localhost:3000
```

---

## 数据库模型

### projects — 项目表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT (UUID) | 主键 |
| name | TEXT | 项目名称 |
| novel_type | TEXT | 小说类型（都市言情/玄幻修仙/...） |
| core_elements | TEXT | 核心元素（JSON 数组） |
| outline | TEXT | AI 生成的大纲 |
| target_word_count | INTEGER | 目标字数 |
| created_at / updated_at | TIMESTAMP | 时间戳 |

### chapters — 章节表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT (UUID) | 主键 |
| project_id | TEXT | 所属项目 |
| number | INTEGER | 章节序号 |
| title | TEXT | 章节标题 |
| content | TEXT | 正文内容 |
| status | TEXT | 状态（draft/writing/completed） |
| word_count | INTEGER | 字数统计 |
| tension_score | FLOAT | 张力评分（0-1） |
| timeline_order | INTEGER | 时间线顺序 |
| synopsis | TEXT | 章节简介 |
| key_events | TEXT | 关键事件（JSON） |
| char_statuses | TEXT | 角色状态快照（JSON） |

### chapter_summaries — 章节摘要表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT (UUID) | 主键 |
| chapter_id | TEXT | 所属章节（唯一） |
| content_summary | TEXT | 内容摘要 |
| plot_progression | TEXT | 情节推进 |
| character_arcs | TEXT | 角色弧线变化 |
| foreshadows_triggered | TEXT | 触发的伏笔 |
| word_count | INTEGER | 字数 |

### chapter_dependencies — 章节依赖表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT (UUID) | 主键 |
| project_id | TEXT | 所属项目 |
| chapter_id | TEXT | 当前章节 |
| depends_on_id | TEXT | 依赖的章节 |
| dependency_type | TEXT | 依赖类型（sequential/reference/contrast） |

### characters — 角色表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT (UUID) | 主键 |
| project_id | TEXT | 所属项目 |
| name | TEXT | 角色名 |
| alias | TEXT | 别名 |
| personality | TEXT | 性格描述 |
| speech_style | TEXT | 说话风格 |
| forbidden_topics | TEXT | 禁忌话题（JSON） |

### character_relations — 角色关系表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT (UUID) | 主键 |
| character_a_id / character_b_id | TEXT | 关系双方 |
| relation_type | TEXT | 关系类型（朋友/敌人/爱人/师徒...） |

### foreshadows — 伏笔表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT (UUID) | 主键 |
| project_id | TEXT | 所属项目 |
| chapter_id | TEXT | 埋下的章节 |
| keyword | TEXT | 伏笔关键词 |
| description | TEXT | 描述 |
| status | TEXT | 状态（planted/triggered/resolved） |

---

## API 路由

### 项目管理 `/api/db/projects`
- `GET /projects` — 获取所有项目
- `POST /projects` — 创建项目
- `GET /projects/{id}` — 获取项目详情
- `PUT /projects/{id}` — 更新项目
- `DELETE /projects/{id}` — 删除项目

### 章节管理 `/api/db/chapters`
- `POST /chapters` — 创建章节
- `GET /chapters/{id}` — 获取章节
- `PUT /chapters/{id}` — 更新章节
- `DELETE /chapters/{id}` — 删除章节
- `POST /chapters/{id}/versions` — 保存版本快照
- `GET /chapters/{id}/versions` — 获取版本历史
- `POST /chapters/{id}/rollback/{version}` — 回滚到指定版本
- `POST /chapters/{id}/summary` — 创建/更新章节摘要
- `GET /chapters/{id}/summary` — 获取章节摘要

### 角色管理 `/api/db/characters`
- `POST /characters` — 创建角色
- `GET /characters/project/{pid}` — 获取项目角色
- `PUT /characters/{id}` — 更新角色
- `DELETE /characters/{id}` — 删除角色

### 伏笔管理 `/api/db/foreshadows`
- `POST /foreshadows` — 创建伏笔
- `GET /foreshadows/project/{pid}` — 获取项目伏笔
- `PUT /foreshadows/{id}` — 更新伏笔状态

### 写作 `/api/writing`
- `POST /` — 流式写作（续写/润色/改写/概括）
  - Body: `{"chapter_id": "...", "instruction": "...", "context": "..."}`
  - 返回: SSE 流式数据 `data: {"type": "chunk", "content": "..."}`

### 进度追踪 `/api/db/project/{id}`
- `GET /progress` — 获取项目进度（章节完成数/字数/伏笔状态）
- `GET /writable-chapters` — 获取可写的章节

---

## 核心功能

### 1. 引导式工作流
```
项目列表 → 新建项目 → 选择小说类型 → 选择核心元素(≤3)
       → 5阶段 AI 生成大纲 → 章节管理 → 写作
```

**5阶段大纲生成**：
1. 生成故事主线
2. 生成章节标题（8-12章）
3. 生成角色列表（JSON）
4. 生成角色关系（JSON）
5. 生成伏笔（JSON）

### 2. 实时张力分析
写作时分析四个维度（0-1）：
- **冲突值**：矛盾强度
- **悬念值**：悬念设置
- **情感值**：情感张力
- **节奏值**：节奏起伏
- **综合张力**：加权平均

### 3. 流式写作
使用 Anthropic SDK 实现 MiniMax 流式输出：
- 续写 / 润色 / 改写 / 概括
- 实时显示生成内容
- 自动上下文构建（项目背景 + 章节信息）

---

## 环境变量（.env）

```bash
MINIMAX_API_KEY=your_api_key_here
TIMEOUT=60
MAX_TOKENS=16384
TEMPERATURE=0.7
```

---

## 已知问题 / 待改进

1. **第二章写作时标题问题**：上下文构建时章节信息获取有误
2. **大纲解析边界情况**：某些大纲格式可能导致解析失败
3. **服务稳定性**：生产环境建议使用 nginx + systemd

---

## 更新日志

### 2026-04-14
- 简化为仅使用 MiniMax Anthropic SDK
- 5阶段增量大纲生成
- 新增章节摘要/依赖/进度追踪功能
- 修复 CORS / foreshadow API 等问题

### 2026-04-12
- 初始版本
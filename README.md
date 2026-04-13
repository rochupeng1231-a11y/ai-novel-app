# AI 写小说应用

> 集成 AI 生成、实时张力分析、多维度回退的小说写作工具

**服务地址**: http://192.168.5.171:3000

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | 原生 HTML/CSS/JS（无框架，模块化） |
| 后端 | FastAPI + Pydantic |
| AI | MiniMax API（`MiniMax-M2.7` 模型） |
| 数据库 | SQLite（`ai_novel.db`） |
| Web 服务器 | nginx（端口 3000，反向代理到 8000） |

---

## 项目结构

```
ai-novel-app/
├── frontend/                    # 前端资源（部署在 /var/www/ai-novel/）
│   ├── index.html               # 入口页面（HTML 结构）
│   ├── app.js                   # 主应用逻辑（UI 状态、API 调用、事件绑定）
│   ├── components/              # 前端组件
│   │   ├── ChapterList.js       # 章节列表组件
│   │   ├── TensionMeter.js       # 张力仪表盘组件
│   │   ├── RelationGraph.js      # 人物关系图谱组件
│   │   └── KnowledgeBase.js      # 知识库面板组件
│   └── styles/                  # 样式表
│       ├── base.css             # 基础样式（重置、变量）
│       ├── layout.css           # 布局样式（三栏、响应式）
│       └── components.css       # 组件样式
│
├── backend/                     # 后端（uvicorn 端口 8000）
│   ├── main.py                  # FastAPI 入口、CORS 配置、路由注册
│   ├── api/                     # API 路由层
│   │   ├── chapters.py          # 章节 CRUD 路由
│   │   ├── characters.py        # 角色 CRUD 路由
│   │   ├── writing.py          # AI 生成（大纲/续写）路由
│   │   ├── database.py         # 项目/数据库路由
│   │   └── rollback.py         # 多维度回退路由
│   ├── services/                # 业务逻辑层
│   │   ├── ai_client.py         # MiniMax API 客户端（httpx）
│   │   ├── writing_engine.py   # 写作引擎（任务队列、Prompt 构造）
│   │   ├── tension_analyzer.py  # 实时张力分析（冲突/悬念/情感/节奏）
│   │   ├── version_control.py  # 版本控制（乐观锁、变更追踪）
│   │   └── rollback_engine.py  # 多维度回退引擎
│   └── models/
│       └── schemas.py          # Pydantic 数据模型
│
├── database/
│   ├── schema.sql              # SQLite 表结构
│   └── models.py              # SQLAlchemy 模型
│
├── tests/                      # 单元测试
│   ├── run_tests.py            # 测试运行器
│   ├── backend/
│   │   ├── api/
│   │   │   ├── test_chapters.py
│   │   │   ├── test_characters.py
│   │   │   └── test_writing.py
│   │   └── services/
│   │       ├── test_ai_client.py
│   │       ├── test_tension_analyzer.py
│   │       └── test_version_control.py
│   └── frontend/
│       └── test_TensionMeter.js
│
├── docs/
│   └── MVP_SPEC.md             # 功能规格说明
│
├── .env                        # 环境变量（API 密钥等）
├── start.sh                    # 服务启动脚本（start/stop/restart/status）
└── requirements.txt            # Python 依赖
```

---

## 数据库表结构

### `projects` — 项目表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT (UUID) | 主键 |
| name | TEXT | 项目名称 |
| description | TEXT | 描述 |
| novel_type | TEXT | 小说类型（都市言情/玄幻修仙/...） |
| core_elements | TEXT | 核心元素（JSON 数组，最多3个） |
| target_word_count | INTEGER | 目标字数 |
| outline | TEXT | AI 生成的大纲（JSON） |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### `chapters` — 章节表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT (UUID) | 主键 |
| project_id | TEXT | 所属项目 |
| title | TEXT | 章节标题 |
| content | TEXT | 正文内容 |
| word_count | INTEGER | 字数 |
| order_index | INTEGER | 章节顺序 |
| version | INTEGER | 版本号（乐观锁） |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### `characters` — 角色表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT (UUID) | 主键 |
| project_id | TEXT | 所属项目 |
| name | TEXT | 角色名 |
| role | TEXT | 角色类型（ protagonist/antagonist/supporting...） |
| description | TEXT | 角色描述 |
| traits | TEXT | 性格特征（JSON） |
| appearance | TEXT | 外貌 |
| backstory | TEXT | 背景故事 |
| relationships | TEXT | 关系（JSON） |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### `versions` — 版本表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT (UUID) | 主键 |
| chapter_id | TEXT | 所属章节 |
| content | TEXT | 版本内容 |
| version_num | INTEGER | 版本号 |
| change_summary | TEXT | 变更摘要 |
| created_at | TIMESTAMP | 创建时间 |

### `foreshadows` — 伏笔表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT (UUID) | 主键 |
| project_id | TEXT | 所属项目 |
| content | TEXT | 伏笔内容 |
| status | TEXT | 状态（pending/fulfilled） |
| created_at | TIMESTAMP | 创建时间 |

### `relations` — 角色关系表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT (UUID) | 主键 |
| project_id | TEXT | 所属项目 |
| character_id | TEXT | 角色 |
| related_id | TEXT | 关联角色 |
| relation_type | TEXT | 关系类型（family/rival/lover...） |

---

## API 路由

### `/api/db/` — 项目管理
- `GET /projects` — 获取所有项目
- `POST /projects` — 创建项目
- `GET /projects/{id}` — 获取项目详情
- `PUT /projects/{id}` — 更新项目
- `DELETE /projects/{id}` — 删除项目
- `PUT /projects/{id}/outline` — 更新大纲

### `/api/chapters/` — 章节管理
- `GET /projects/{project_id}/chapters` — 获取章节列表
- `POST /projects/{project_id}/chapters` — 创建章节
- `PUT /chapters/{id}` — 更新章节
- `DELETE /chapters/{id}` — 删除章节

### `/api/characters/` — 角色管理
- `GET /projects/{project_id}/characters` — 获取角色列表
- `POST /projects/{project_id}/characters` — 创建角色
- `PUT /characters/{id}` — 更新角色
- `DELETE /characters/{id}` — 删除角色

### `/api/writing/` — AI 写作
- `POST /` — 生成内容（大纲/续写）
  - Body: `{"chapter_id": "...", "instruction": "...", "context": "..."}`
  - 返回: `{"content": "...", "tension_score": 0.x, "tokens_used": n}`

### `/api/rollback/` — 多维度回退
- `POST /` — 执行回退
  - Body: `{"project_id": "...", "chapter_id": "...", "dimension": "content|character|logic|all"}`

---

## 核心功能说明

### 1. 引导式工作流
```
项目列表 → 新建项目 → 选择小说类型 → 选择核心元素(≤3) → AI 生成大纲 → 章节管理 → 写作
```
- 6 种预设类型：都市言情、玄幻修仙、悬疑推理、科幻未来、武侠江湖、校园青春
- 10 种预设元素：逆袭崛起、命中注定、商战博弈等

### 2. 实时张力分析
写作时实时分析四个维度：
- **冲突值**：矛盾强度（0-1）
- **悬念值**：悬念设置（0-1）
- **情感值**：情感张力（0-1）
- **节奏值**：节奏起伏（0-1）
- **综合张力**：加权平均

### 3. 多维度回退引擎
支持按维度回退：
- `content` — 仅内容回退
- `character` — 角色一致性回退
- `logic` — 逻辑连贯性回退
- `all` — 全维度回退

---

## 服务管理

### 启动服务
```bash
# 方法1：使用启动脚本
/root/.openclaw/agents/team-leader/workspace/ai-novel-app/start.sh start

# 方法2：手动启动
cd /root/.openclaw/agents/team-leader/workspace/ai-novel-app
nohup .venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000 > /tmp/uvicorn.log 2>&1 &
nginx
```

### 重启服务
```bash
/root/.openclaw/agents/team-leader/workspace/ai-novel-app/start.sh restart
```

### 查看状态
```bash
/root/.openclaw/agents/team-leader/workspace/ai-novel-app/start.sh status
ps aux | grep uvicorn | grep -v grep
```

### 相关路径
- 前端部署：`/var/www/ai-novel/`（nginx 直接托管）
- 后端代码：`/root/.openclaw/agents/team-leader/workspace/ai-novel-app/backend/`
- 数据库：`/root/.openclaw/agents/team-leader/workspace/ai-novel-app/ai_novel.db`
- nginx 配置：`/etc/nginx/sites-available/ai-novel`

---

## 环境变量（.env）

```bash
MINIMAX_API_KEY=your_api_key_here
MINIMAX_GROUP_ID=your_group_id_here
```

---

## 使用 Claude Code 开发

Claude Code 建议在 `backend/` 目录下工作：
```bash
cd /root/.openclaw/agents/team-leader/workspace/ai-novel-app
```

常用命令：
```bash
# 运行测试
.venv/bin/python tests/run_tests.py

# 启动后端（开发模式，自动 reload）
cd /root/.openclaw/agents/team-leader/workspace/ai-novel-app
.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# 查看 uvicorn 日志
tail -f /tmp/uvicorn.log

# 数据库查看
sqlite3 ai_novel.db ".schema"
```

---

## 已知问题 / 待改进

1. **服务稳定性**：uvicorn 依赖后台进程，偶尔需要 restart.sh 重启（已配置 PID 文件）
2. **app.js 源文件为空**：源文件 `/root/.openclaw/agents/team-leader/workspace/ai-novel-app/frontend/app.js` 为 0 字节，部署文件在 `/var/www/ai-novel/app.js`
3. **前端框架**：目前是原生 JS，建议迁移到 React/Vue 提升可维护性
4. **数据库**：当前是 SQLite，多用户场景建议迁移到 PostgreSQL
5. **AI 模型**：当前仅支持 MiniMax，可扩展支持 Claude/GPT 等
6. **用户认证**：暂无用户系统，数据共享同一数据库

---

## 部署记录（2026-04-12）

- nginx 监听 3000 端口，反向代理 `/api/` 到 8000
- 前端文件复制到 `/var/www/ai-novel/`（nginx 无法访问 `/root/`）
- 已创建测试项目："测试小说2"、"我的小说"、"我的都市小说"

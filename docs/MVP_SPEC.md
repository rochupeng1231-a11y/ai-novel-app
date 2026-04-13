# AI 写小说应用 - MVP 功能规格

> 版本：v0.1  
> 日期：2026-04-12

---

## 一、MVP 目标

在 1-2 个月内实现核心写作流程跑通，支持单用户、单项目。

---

## 二、功能范围

### 2.1 必须实现（MVP）

| 模块 | 功能 | 优先级 |
|-----|------|--------|
| **项目管理** | 新建/打开/删除小说项目 | P0 |
| **章节管理** | 创建/编辑/删除章节 | P0 |
| **写作区** | 富文本编辑，续写/润色/改写/概括 | P0 |
| **角色卡** | 创建/编辑角色，含性格、语气、禁区 | P0 |
| **张力仪表盘** | 实时四维张力分析（冲突/悬念/情感/节奏） | P1 |
| **版本管理** | 手动保存版本，历史版本回退 | P1 |

### 2.2 暂不实现（后续迭代）

- RAG 检索系统
- 多模型路由
- 关联回退
- 协作功能
- 多用户/订阅系统

---

## 三、技术方案

### 3.1 技术栈

| 层级 | 技术 | 说明 |
|-----|------|------|
| 前端 | 原生 HTML/CSS/JS | 无框架依赖，快速原型 |
| 后端 | FastAPI + Python | 高性能 API |
| 数据库 | SQLite（开发）→ PostgreSQL（生产） | 简化部署 |
| AI API | Kimi / Claude（预留接口） | 写作生成 |

### 3.2 项目结构

```
ai-novel-app/
├── frontend/
│   ├── index.html          # 入口
│   ├── app.js              # 主逻辑
│   ├── styles/             # CSS模块
│   └── components/         # JS组件
├── backend/
│   ├── main.py             # FastAPI入口
│   ├── api/                # API路由
│   ├── services/           # 业务逻辑
│   └── models/             # 数据模型
├── database/
│   └── schema.sql          # 表结构
├── docs/
│   └── MVP_SPEC.md         # 本文档
└── requirements.txt        # Python依赖
```

### 3.3 数据库

- 开发阶段：SQLite（零配置）
- 生产阶段：PostgreSQL

**核心表：**
- projects（项目）
- chapters（章节）
- characters（角色）
- character_relations（角色关系）
- chapter_versions（版本记录）

---

## 四、API 设计

### 4.1 章节 API

```
POST   /api/chapters          创建章节
GET    /api/chapters/project/:pid   获取项目所有章节
GET    /api/chapters/:id      获取单个章节
PUT    /api/chapters/:id      更新章节
DELETE /api/chapters/:id      删除章节
```

### 4.2 角色 API

```
POST   /api/characters         创建角色
GET    /api/characters/project/:pid   获取项目所有角色
GET    /api/characters/:id     获取单个角色
PUT    /api/characters/:id     更新角色
DELETE /api/characters/:id     删除角色
```

### 4.3 写作 API

```
POST   /api/writing            执行写作指令
```

请求：
```json
{
  "chapter_id": "xxx",
  "instruction": "续写",
  "context": "额外上下文"
}
```

响应：
```json
{
  "content": "生成的文本",
  "tension_score": 0.75,
  "tokens_used": 500
}
```

---

## 五、交互流程

### 5.1 写作流程

1. 用户选择/创建章节
2. 在编辑区输入内容
3. 点击「续写/润色/改写/概括」
4. AI 生成内容追加/替换到编辑区
5. 可手动保存版本
6. 张力仪表盘实时显示当前文本的张力

### 5.2 角色管理流程

1. 在角色面板点击「新建角色」
2. 填写角色名称、性格、语气、禁区
3. 角色出现在关系图谱中
4. 可建立角色间的关系

---

## 六、验收标准

### 6.1 功能验收

- [ ] 可以创建项目
- [ ] 可以创建章节
- [ ] 可以编辑章节内容
- [ ] 可以创建角色
- [ ] 可以建立角色关系
- [ ] 续写功能有返回结果（可以是模拟的）
- [ ] 张力仪表盘有数据显示
- [ ] 可以保存版本

### 6.2 性能要求

- 页面加载 < 2秒
- 写作指令响应（模拟）< 1秒
- 张力分析 < 500ms

### 6.3 界面要求

- 暗黑主题
- 响应式布局（适配 1280px+）
- 操作按钮可见可点击
- 文字清晰可读

---

## 七、下一步

- [ ] 确认 MVP 范围
- [ ] 搭建开发环境
- [ ] 实现后端 CRUD API
- [ ] 实现写作模拟接口
- [ ] 前后端联调
- [ ] 内部测试

---

*待补充*

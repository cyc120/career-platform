# 职途无限 (INFINITE PATH) — AI 职业规划平台

基于 LangGraph 多智能体 + RAG 检索增强生成的一站式职业规划系统，提供简历分析、岗位匹配、职业规划、学习计划、报告生成五大核心能力。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Element Plus + ECharts + AntV G6 |
| 后端 | FastAPI + LangGraph + LangChain + SQLAlchemy 2.0 |
| LLM | DeepSeek (deepseek-chat) / 通义千问 (qwen-plus) |
| 向量检索 | ChromaDB + BGE-small-zh 嵌入模型 |
| 知识图谱 | Neo4j 5 |
| 数据库 | SQLite（本地开发）/ MySQL 8.0（Docker 部署）|
| 缓存/队列 | Redis 7（Docker）/ 内存字典（本地开发）|
| 异步任务 | ARQ (Redis Queue) |

---

## 系统架构

```
                         ┌─────────────────────┐
                         │   Vue 3 前端 (5173)   │
                         │  Element Plus + ECharts│
                         └──────────┬──────────┘
                                    │ /api proxy
                                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       FastAPI 后端 (:8000)                           │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │              AgentHarness (单例调度器)                          │  │
│  │   SHA-256 缓存 · 指数退避重试 · 超时控制 · 运行追踪            │  │
│  └──────────────────────────┬─────────────────────────────────────┘  │
│                              │                                       │
│  ┌────────┬────────┬────────┬┴───────┬────────┐                     │
│  │ 简历   │ 岗位   │ 职业   │ 学习   │ 报告   │                     │
│  │ 分析   │ 匹配   │ 规划   │ 计划   │ 生成   │                     │
│  │ Agent  │ Agent  │ Agent  │ Agent  │ Agent  │                     │
│  └────────┴────────┴────────┴────────┴────────┘                     │
│                                                                      │
│  共享基础设施: LLM工厂 · 重试工具 · RAG检索 · 数据库 · Redis        │
└──────────────────────────────────────────────────────────────────────┘
         │              │              │
         ▼              ▼              ▼
    ChromaDB        Neo4j         SQLite/MySQL
   (向量检索)     (知识图谱)       (持久存储)
```

### 五大核心智能体

| 智能体 | agent_id | 节点数 | LLM调用 | 超时 | 可缓存 |
|--------|----------|--------|---------|------|--------|
| 简历分析 | `resume_analyzer` | 9 | 3~5 次 | 300s | 是 |
| 岗位匹配 | `job_matcher` | 7 | 0 次 (子模块间接调用) | 300s | 否 |
| 职业规划 | `career_planner` | 6 | 2 次 | 300s | 是 |
| 学习计划 | `learning_plan` | 8 | 1 次/action | 300s | 是 |
| 报告生成 | `report` | 4 | 1 次 | 180s | 否 |

### 直接 LLM 端点（不经过 Harness）

| 端点 | 说明 |
|------|------|
| `POST /diagnosis/generate` | AI 深度诊断（雷达图 → 文字报告） |
| `POST /coach/chat` | 职业教练对话 |
| `POST /generate/resume` | AI 简历生成 |
| `GET /learning/daily-tasks` | 每日学习任务 |

### 数据流

```
上传简历 → resume_analyzer → 用户画像 (7维雷达图)
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
              job_matcher    diagnosis API   用户查看报告
                    │
                    ▼
              匹配结果 Top5
                    │
           ┌────────┴────────┐
           ▼                 ▼
    career_planner    learning_plan
           │                 │
           ▼                 ▼
     career_plans      daily_tasks
           │                 │
           └────────┬────────┘
                    ▼
              report 智能体 → 完整报告 (TXT/Word/PDF)
```

---

## 快速开始

### 方式一：本地开发（SQLite + 内存缓存，无需 Docker）

#### 1. 后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，设置 OPENAI_API_KEY（DeepSeek API Key）
# DB_BACKEND 默认为 sqlite，无需修改
```

启动后端：

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

首次启动自动完成：
- 创建 SQLite 数据库 `career_platform.db` 并建表
- 导入种子数据（测试用户、示例岗位、晋升路径）
- 后台构建 ChromaDB 向量索引

API 文档：http://localhost:8000/docs

#### 2. 前端

```bash
cd career-front-main

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问 http://localhost:5173

Vite 开发代理自动将 `/api` 请求转发到 `http://localhost:8000`。

#### 3. 测试账号

| 用户名 | 密码 |
|--------|------|
| `testuser` | `password123` |

首次访问时，前端会自动获取 Guest Token，也可手动注册新账号。

---

### 方式二：Docker Compose 全栈部署

#### 1. 配置环境变量

```bash
cd backend
cp .env.example .env
# 编辑 .env，关键修改：
#   DB_BACKEND=mysql
#   MYSQL_HOST=backend-mysql
#   MYSQL_PASSWORD=root
#   REDIS_URL=redis://backend-redis:6379/0
#   NEO4J_URI=bolt://backend-neo4j:7687
```

#### 2. 启动

```bash
docker compose up -d
```

启动 6 个容器：

| 容器 | 端口 | 说明 |
|------|------|------|
| `backend-mysql` | 3306 | MySQL 8.0 数据库 |
| `backend-neo4j` | 7474 / 7687 | Neo4j 知识图谱 |
| `backend-redis` | 6379 | Redis 缓存/队列 |
| `career-backend` | 8000 | FastAPI 后端 |
| `arq-worker` | - | 异步智能体任务 |
| `career-frontend` | 80 | Nginx 静态前端 |

访问 http://localhost 即可使用。

---

## 环境变量

在 `backend/.env` 中配置（参考 `.env.example`）：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OPENAI_API_KEY` | DeepSeek API Key | （必填） |
| `OPENAI_BASE_URL` | LLM API 地址 | `https://api.deepseek.com/v1` |
| `OPENAI_MODEL` | LLM 模型名 | `deepseek-chat` |
| `OPENAI_EMBEDDING_MODEL` | 嵌入模型 | `BAAI/bge-small-zh-v1.5` |
| `DB_BACKEND` | 数据库类型 | `sqlite` |
| `MYSQL_HOST` | MySQL 地址 | `localhost` |
| `MYSQL_PORT` | MySQL 端口 | `3306` |
| `MYSQL_USER` | MySQL 用户 | `root` |
| `MYSQL_PASSWORD` | MySQL 密码 | `root` |
| `MYSQL_DATABASE` | MySQL 数据库 | `career_platform` |
| `NEO4J_URI` | Neo4j 连接地址 | `bolt://localhost:7687` |
| `NEO4J_USER` | Neo4j 用户 | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j 密码 | `password` |
| `REDIS_URL` | Redis 地址 | `redis://localhost:6379/0` |
| `CHROMA_PERSIST_DIR` | ChromaDB 存储路径 | `./chroma_data` |
| `JWT_SECRET_KEY` | JWT 签名密钥 | `change-me` |
| `JWT_EXPIRE_MINUTES` | Access Token 有效期 | `1440` (24h) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh Token 有效期 | `7` |
| `AGENT_MAX_RETRIES` | 智能体最大重试次数 | `3` |
| `AGENT_TIMEOUT_SECONDS` | 智能体超时时间 | `300` |
| `UPLOAD_DIR` | 文件上传目录 | `./uploads` |
| `HF_ENDPOINT` | HuggingFace 镜像 | `https://hf-mirror.com` |

**说明**：本地开发模式（`DB_BACKEND=sqlite`）下，Neo4j、Redis 均为可选组件，系统会自动降级到内存实现。

---

## API 端点一览

### 认证 `/api/v1/auth`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/auth/guest-token` | 获取游客 Token |
| POST | `/auth/register` | 注册 |
| POST | `/auth/login` | 登录 |
| POST | `/auth/refresh` | 刷新 Token |
| POST | `/auth/logout` | 登出 |

### 简历 `/api/v1/resume`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/resume/extract` | 上传简历文件提取文本 |
| POST | `/resume/supplement` | 补充简历信息 |
| POST | `/resume/analyze` | 分析简历生成画像 |

### 岗位匹配 `/api/v1/matching`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/matching/match` | 执行人岗匹配 |
| POST | `/matching/select-job` | 锁定目标岗位 |
| GET | `/matching/selected-job` | 获取已锁定岗位 |
| GET | `/matching/has-matching` | 检查匹配数据 |
| GET | `/matching/capability-model` | 获取能力模型 |
| GET | `/matching/job-graph` | 获取岗位知识图谱 |

### 职业规划 `/api/v1/career-plan`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/career-plan/` | 生成职业规划 |

### 学习计划 `/api/v1/learning-plan`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/learning-plan/generate` | 生成学习计划 |
| GET | `/learning-plan/daily-tasks` | 获取每日任务 |
| POST | `/learning-plan/polish` | 润色学习计划 |
| POST | `/learning-plan/adjust` | 调整学习任务 |
| POST | `/learning-plan/export` | 导出学习计划 |

### 岗位 `/api/v1/jobs`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/jobs/` | 岗位列表（支持 RAG 筛选） |
| GET | `/jobs/search` | 语义搜索岗位 |
| GET | `/jobs/hot` | 热门岗位 |
| GET | `/jobs/{job_id}` | 岗位详情 |

### 收藏 `/api/v1/favorites`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/favorites/` | 收藏列表 |
| POST | `/favorites/` | 添加收藏 |
| DELETE | `/favorites/{job_id}` | 取消收藏 |

### 诊断 `/api/v1/diagnosis`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/diagnosis/generate` | AI 深度诊断报告 |

### 报告 `/api/v1/report`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/report/generate` | 生成完整报告 |
| POST | `/report/polish` | AI 润色报告 |
| GET | `/report/load` | 加载已有报告 |
| POST | `/report/export` | 导出报告 (txt/docx/pdf) |

### 其他

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/v1/agents` | 已注册智能体列表 |

---

## 项目结构

```
career-platform/
├── backend/                          # FastAPI 后端
│   ├── app/
│   │   ├── main.py                   # 应用入口
│   │   ├── config.py                 # 配置管理 (pydantic-settings)
│   │   ├── api/v1/                   # API 路由
│   │   │   ├── auth.py               #   认证
│   │   │   ├── resume.py             #   简历
│   │   │   ├── matching.py           #   岗位匹配
│   │   │   ├── career_plan.py        #   职业规划
│   │   │   ├── learning_plan.py      #   学习计划
│   │   │   ├── report.py             #   报告生成
│   │   │   ├── diagnosis.py          #   AI 诊断
│   │   │   ├── jobs.py               #   岗位查询
│   │   │   ├── favorites.py          #   收藏
│   │   │   └── agents.py             #   智能体管理
│   │   ├── agents/                   # LangGraph 智能体
│   │   │   ├── base.py               #   智能体基类
│   │   │   ├── harness.py            #   AgentHarness 调度器
│   │   │   ├── registry.py           #   智能体注册
│   │   │   ├── llm_factory.py        #   LLM 实例工厂
│   │   │   ├── retry.py              #   重试工具
│   │   │   ├── resume_analyzer/      #   简历分析智能体
│   │   │   ├── job_matcher/          #   岗位匹配智能体
│   │   │   ├── career_planner/       #   职业规划智能体
│   │   │   ├── learning_plan/        #   学习计划智能体
│   │   │   └── report/               #   报告生成智能体
│   │   ├── rag/                      # RAG 检索模块
│   │   │   ├── embedding.py          #   嵌入模型
│   │   │   ├── vector_store.py       #   ChromaDB 向量库
│   │   │   ├── retrievers.py         #   检索器
│   │   │   ├── ingest_jobs.py        #   岗位数据导入
│   │   │   └── ingest_learning.py    #   学习资源导入
│   │   ├── db/                       # 数据库连接
│   │   │   ├── mysql.py              #   SQLAlchemy 引擎
│   │   │   ├── neo4j.py              #   Neo4j 管理器
│   │   │   ├── redis.py              #   Redis 连接
│   │   │   └── memory_store.py       #   内存缓存 (Redis 降级)
│   │   ├── models/                   # ORM 模型
│   │   ├── schemas/                  # Pydantic 数据模型
│   │   ├── middleware/               # 中间件 (认证/限流/错误)
│   │   └── utils/                    # 工具函数
│   ├── scripts/
│   │   └── init_db.sql               # 数据库初始化脚本
│   ├── requirements.txt              # Python 依赖
│   ├── docker-compose.yml            # Docker 编排
│   └── .env.example                  # 环境变量模板
│
├── career-front-main/                # Vue 3 前端
│   ├── src/
│   │   ├── views/                    # 页面
│   │   │   ├── Home.vue              #   首页
│   │   │   ├── Jobs/                 #   岗位浏览/详情
│   │   │   └── Profile/              #   个人中心
│   │   │       ├── PersonalInfo.vue  #     个人画像
│   │   │       ├── JobMatch.vue      #     岗位匹配
│   │   │       ├── GrowthTracker.vue #     学习计划
│   │   │       ├── FavoriteJobs.vue  #     收藏岗位
│   │   │       ├── PolishAndExport.vue#    报告导出
│   │   │       └── AIReport.vue      #     AI 报告
│   │   ├── components/               # 组件
│   │   │   ├── RadarChart.vue        #   雷达图
│   │   │   ├── JobKnowledgeGraph.vue #   知识图谱
│   │   │   ├── PromotionGraph.vue    #   晋升路径图
│   │   │   ├── InteractiveLoading.vue#   加载动画
│   │   │   └── JobCard.vue           #   岗位卡片
│   │   ├── api/                      # API 调用层
│   │   ├── stores/                   # Pinia 状态管理
│   │   └── router/                   # 路由配置
│   ├── package.json
│   └── vite.config.js
│
├── 智能体图流程详解.md                # 智能体流程详细文档
└── 智能体流程图.md                    # 智能体流程图
```

---

## 数据库表结构

| 表名 | 说明 |
|------|------|
| `users` | 用户账号 |
| `jobs` | 岗位列表 |
| `user_profiles` | 用户画像 (JSON) |
| `matching_report` | 岗位匹配结果 |
| `user_selected_job` | 锁定的目标岗位 |
| `career_plans` | 职业规划 |
| `learning_plans` | 学习计划 |
| `daily_tasks` | 每日学习任务 |
| `user_reports` | 生成的完整报告 |
| `favorites` | 收藏岗位 |
| `job_profiles` | LLM 生成的岗位画像 |
| `promotion_transition` | 晋升路径 |
| `agent_runs` | 智能体运行记录 |
| `chat_history` | 对话历史 |

---

## 核心机制

### AgentHarness 调度器

所有智能体通过 `AgentHarness` 单例统一管理：

```python
harness.register(agent)                    # 注册智能体
result = await harness.run(agent_id, input_data, user_id)  # 执行
```

内置能力：
- **SHA-256 缓存**：相同输入直接返回缓存结果
- **指数退避重试**：1s → 2s → 4s，最多 3 次
- **超时控制**：每个智能体独立超时配置
- **运行追踪**：记录每次执行状态和耗时

### RAG 检索增强

岗位匹配和学习计划使用 ChromaDB 向量检索：

1. **岗位向量化**：启动时将所有岗位描述导入 ChromaDB
2. **语义搜索**：根据用户画像检索 top_k 相关岗位
3. **混合匹配**：向量相似度 + LLM 评分综合排序

### 降级策略

| 组件 | 降级方案 |
|------|----------|
| Redis | 内存字典（`memory_store.py`） |
| Neo4j | 跳过图谱增强，直接进入下一步 |
| LLM 失败 | 返回本地算法兜底结果 |
| 证书评分 | 纯算法，不依赖 LLM |

---

## 相关文档

- [智能体流程图](智能体流程图.md) — 系统总框架 + 五大智能体流程 + 子模块详解
- [智能体图流程详解](智能体图流程详解.md) — 每个智能体的节点、参数、Prompt 详细说明

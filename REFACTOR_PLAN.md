# Career Service AI Platform — 后端重构 + 前后端打通 完整计划

## Context

当前系统是一个职业规划 AI 平台，包含 Python Flask 后端（5 个 DeepSeek Agent）和 Vue 3 前端（全 mock 数据），部署在 MySQL + Neo4j 环境。代码审查发现 11 个致命 Bug（表缺失、列名不匹配、DB 名不一致、NameError 等），架构混乱（AgentBase 未用、AgentManager 不全、重复目录、无认证、无配置中心）。

重构目标：
1. Flask → FastAPI
2. 手动 Agent 链 → LangGraph StateGraph
3. 全 mock 前端 → 真实 API 调用
4. 新增：Agent Harness 编排层、RAG 知识库、Redis 缓存/队列/限流

---

## 新增架构决策

### Agent Harness 编排层
在 LangGraph 之上增加 `AgentHarness` 中央执行引擎，统一管理：
- **Agent 生命周期**：注册→调度→执行→状态持久化→结果聚合→监控
- **异步任务分发**：长任务（岗位匹配、报告生成）通过 Redis 队列异步执行
- **执行追踪**：每次 Agent 运行记录到 MySQL，含状态、耗时、输入输出摘要
- **错误恢复**：失败自动重试（最多 3 次），死信队列兜底

### RAG 知识库
- **向量数据库**：ChromaDB（轻量、Python 原生，适合本场景）
- **Embedding**：DeepSeek Embedding API 或本地 BGE 模型
- **三个检索场景**：
  1. 岗位语义检索：所有岗位描述向量化，支持语义搜索（替代当前 `LIKE` 模糊查询）
  2. 简历-岗位混合匹配：简历向量 vs 岗位向量 余弦相似度 + LLM 维度打分 双层
  3. 学习资源检索：技术栈文档、课程、知识图谱节点向量化，辅助学习计划生成
- **文档摄入**：系统启动时自动从 MySQL jobs 表构建向量索引，学习资源支持增量添加

### Redis 三层应用
- **会话层**：JWT 白名单/黑名单 + Refresh Token 存储（替代纯无状态 JWT）
- **缓存层**：LLM 分析结果缓存（同输入 → 同输出，TTL 1h，省 DeepSeek API 费）
- **队列层**：Agent 异步任务队列（ARQ + Redis）、API 限流计数器（sliding window）

---

## 目标架构图

```
[Vue 3 SPA] --HTTP--> [FastAPI :8000]
                                                      |
                    +--------------+-------------------+------------------+
                    |              |                   |                  |
               [MySQL 8.0]   [Neo4j 5]          [ChromaDB]          [Redis]
                    |              |                   |                  |
                    +-- 持久化 ----+--- RAG 向量存储 ---+--- 缓存/队列 ----+
                                   |
                          [DeepSeek LLM API]
                                   |
                    +-- API 调用 ---+--- LLM 接口 ----+
                    |
            [LangGraph Agent Graph] × 5
                    |
            [Agent Harness 编排层]
```

---

## Phase 1: 项目骨架 + 基础设施

### 1.1 新目录结构

后端全新目录（保留旧代码在 `carrer-Agents-old/` 做参考）：

```
backend/
  app/
    __init__.py
    main.py                              # FastAPI app factory + lifespan
    config.py                            # 统一配置 (pydantic-settings)
    dependencies.py                      # 依赖注入 (get_db, get_current_user, get_redis)
    
    api/v1/
      __init__.py
      auth.py                            # /auth/register, /login, /refresh, /logout
      agents.py                          # GET /agents (Harness 状态查询)
      resume.py                          # POST /resume/extract, /supplement, /analyze (合并)
      matching.py                        # POST /matching/match
      career_plan.py                     # POST /career-plan
      learning_plan.py                   # /learning-plan/* 全套
      jobs.py                            # GET /jobs, /jobs/{id}, /jobs/search
      favorites.py                       # POST/GET/DELETE /favorites
      
    agents/
      __init__.py
      base.py                            # AgentBase ABC (LangGraph contract)
      harness.py                         # AgentHarness 中央编排引擎 ★NEW★
      registry.py                        # 统一 Agent 注册表
      llm_factory.py                     # 共享 LLM 工厂 (ChatOpenAI + Embeddings)
      
      resume_analyzer/                   # 简历提取+分析 合并 Agent ★合并★
        graph.py, state.py, prompts.py, nodes.py
      job_matcher/                       # 人岗匹配 Agent
        graph.py, state.py, prompts.py, nodes.py, db_utils.py
      career_planner/                    # 职业规划 Agent
        graph.py, state.py, prompts.py, schemas.py, tools.py
      learning_plan/                     # 学习计划 Agent
        graph.py, state.py, prompts.py, schemas.py, tools.py
    
    rag/                                 # ★NEW★ RAG 模块
      __init__.py
      embedding.py                       # DeepSeek Embedding 封装
      vector_store.py                    # ChromaDB 管理 (collection 创建/增删查)
      ingest_jobs.py                     # 岗位描述向量化摄入
      ingest_learning.py                 # 学习资源向量化摄入
      retrievers.py                      # 三个检索器 (job_search, resume_job, learning)
      
    db/
      __init__.py
      mysql.py                           # SQLAlchemy async engine + session
      neo4j.py                           # Neo4j async driver
      redis.py                           # ★NEW★ Redis 连接池 + 工具函数
      migrations/                        # Alembic
        env.py
        versions/001_initial.py
    
    models/                              # SQLAlchemy ORM models
      user.py, job.py, profile.py, favorite.py
      career_plan.py, learning.py, matching.py
      agent_run.py                       # ★NEW★ Agent 执行记录

    schemas/                             # Pydantic request/response
      user.py, resume.py, analysis.py, matching.py
      career_plan.py, learning_plan.py, job.py, favorite.py
    
    middleware/
      error_handler.py                   # 全局异常处理
      rate_limiter.py                    # ★NEW★ Redis sliding window 限流
      auth.py                            # JWT 验证中间件
    
    utils/
      security.py                        # JWT + bcrypt
      file_handler.py                    # 文件上传持久化
      cache.py                           # ★NEW★ Redis 缓存装饰器
      
  scripts/
    init_db.py                           # 建表脚本
    seed_data.py                         # 种子数据（含 bcrypt 密码）
    ingest_all.py                        # ★NEW★ 全量向量化摄入
    
  tests/
    conftest.py                          # async test fixtures
    test_auth.py, test_resume.py, test_matching.py
    test_career_plan.py, test_learning_plan.py
    test_rag.py                          # ★NEW★ 向量检索测试
    
  requirements.txt
  alembic.ini
  .env.example
  pyproject.toml
```

### 1.2 requirements.txt

```
# Framework
fastapi>=0.110.0
uvicorn[standard]>=0.29.0

# LangChain Ecosystem
langchain>=0.3.0
langchain-openai>=0.2.0
langchain-core>=0.3.0
langgraph>=0.2.0
langchain-community>=0.3.0
langchain-chroma>=0.2.0         # ★RAG

# Database
sqlalchemy[asyncio]>=2.0.0
aiomysql>=0.2.0
neo4j>=5.0.0
redis[hiredis]>=5.0.0           # ★Redis
arq>=0.26.0                     # ★Redis async task queue

# Auth
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4

# File & Data
python-multipart>=0.0.9
python-dotenv>=1.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
pypdf>=3.0.0
python-docx>=0.8.11
pytesseract>=0.3.10
Pillow>=10.0.0
matplotlib>=3.7.0

# Migration
alembic>=1.13.0

# Testing
pytest>=8.0.0
pytest-asyncio>=0.24.0
httpx>=0.27.0
```

### 1.3 config.py

```python
class Settings(BaseSettings):
    # LLM
    OPENAI_API_KEY: str
    OPENAI_BASE_URL: str = "https://api.deepseek.com/v1"
    OPENAI_MODEL: str = "deepseek-chat"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-ada-002"  # 或 DeepSeek 等价物
    
    # MySQL
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str
    MYSQL_DATABASE: str = "career_platform"
    
    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str
    
    # Redis ★NEW★
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600          # LLM 结果缓存 1 小时
    REDIS_RATE_LIMIT: int = 60           # 每分钟请求数上限
    
    # ChromaDB ★NEW★
    CHROMA_PERSIST_DIR: str = "./chroma_data"
    CHROMA_COLLECTION_JOBS: str = "job_descriptions"
    CHROMA_COLLECTION_LEARNING: str = "learning_resources"
    
    # JWT
    JWT_SECRET_KEY: str
    JWT_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7   # ★Redis 存储 Refresh Token
    
    # Harness ★NEW★
    AGENT_MAX_RETRIES: int = 3
    AGENT_TIMEOUT_SECONDS: int = 300
    AGENT_ASYNC_WORKERS: int = 4
    
    # Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 16
```

### 1.4 Redis 连接层 (app/db/redis.py)

```python
import redis.asyncio as redis
from app.config import settings

pool = redis.ConnectionPool.from_url(settings.REDIS_URL, max_connections=20)

async def get_redis() -> redis.Redis:
    return redis.Redis(connection_pool=pool)

# Token 黑名单操作
async def blacklist_token(token: str, expire_seconds: int): ...
async def is_token_blacklisted(token: str) -> bool: ...

# 限流计数器（sliding window）
async def check_rate_limit(user_id: str, limit: int, window: int = 60) -> bool: ...

# Agent 结果缓存
async def cache_agent_result(key: str, value: str, ttl: int): ...
async def get_cached_agent_result(key: str) -> str | None: ...
```

## Phase 2: Bug 修复 (Day 2)

### 2.1 修复所有致命 Bug（11 项，详见审查报告）
核心项：
- 补齐 `user_profiles` 和 `favorites` 表（Alembic migration 001）
- 统一数据库名 `career_platform`，修所有列名引用
- `ANALYZE_PROMPT` import 修复

- 删除 `career_planner/career_planner/` 重复目录
- `asyncio.new_event_loop()` → `asyncio.run()`
- `langchain-community` 加入依赖
- 种子数据密码 bcrypt 哈希化

---

## Phase 3: Agent Harness 编排引擎 ★核心新增★

### 3.1 AgentHarness 设计

```
app/agents/harness.py

AgentHarness
├── register(agent_id, graph_builder, config)
├── run(agent_id, input_data) -> RunResult          # 同步执行 + 自动重试
├── run_async(agent_id, input_data) -> JobID        # 异步投递到 Redis 队列
├── get_status(job_id) -> JobStatus                  # 查询异步任务状态
├── get_result(job_id) -> RunResult                  # 获取异步任务结果
├── cancel(job_id) -> bool                           # 取消异步任务
├── list_agents() -> [AgentInfo]
└── get_stats(agent_id) -> AgentStats                # 执行统计
```

- `run()`：同步调用 `graph.ainvoke()` + 执行记录持久化 + 缓存检查
- `run_async()`：序列化参数 → 投递 ARQ Redis 队列 → 返回 job_id → ARQ Worker 消费执行
- 重试逻辑：捕获 `Exception` → 写入 `agent_runs` 表 → 最多重试 3 次（指数退避 1s/4s/16s）
- 缓存：`run()` 执行前先查 `agent_result:{agent_id}:{input_hash}` → 命中则直接返回

### 3.2 AgentRun 追踪表 (app/models/agent_run.py)

```python
class AgentRun(Base):
    id: UUID (PK)
    agent_id: str
    user_id: int
    status: Enum[PENDING, RUNNING, SUCCESS, FAILED, CANCELLED]
    input_hash: str                    # SHA256(input_json) 用于缓存 key
    input_data: JSON
    output_data: JSON (nullable)
    error_message: text (nullable)
    retry_count: int (default 0)
    duration_ms: int (nullable)
    started_at: datetime
    completed_at: datetime (nullable)
    created_at: datetime
```

### 3.3 ARQ Worker（异步 Agent 执行）

```python
# app/worker.py
from arq import create_pool
from arq.connections import RedisSettings

async def run_agent_job(ctx, agent_id: str, user_id: int, input_data: dict):
    harness = AgentHarness()
    return await harness._execute_with_retry(agent_id, user_id, input_data)

# uvicorn 启动时创建 ARQ pool
```

### 3.4 缓存层 (app/utils/cache.py)

```python
from functools import wraps
import hashlib, json
from app.db.redis import get_redis

def cached_agent(ttl: int = 3600):
    """Decorator: cache agent results by input hash"""
    def decorator(func):
        @wraps(func)
        async def wrapper(agent_id: str, input_data: dict, **kwargs):
            key = f"agent_result:{agent_id}:{hash_input(input_data)}"
            r = await get_redis()
            cached = await r.get(key)
            if cached:
                return json.loads(cached)
            result = await func(agent_id, input_data, **kwargs)
            await r.setex(key, ttl, json.dumps(result, default=str))
            return result
        return wrapper
    return decorator

def hash_input(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]
```

---

## Phase 4: RAG 知识库模块 ★新增★

### 4.1 Embedding 工厂 (app/rag/embedding.py)

```python
from langchain_openai import OpenAIEmbeddings
from app.config import settings

def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=settings.OPENAI_EMBEDDING_MODEL,
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
    )
```

如果 DeepSeek 暂不支持 Embedding API，降级方案为：使用 `langchain_community.embeddings.HuggingFaceBgeEmbeddings` 加载本地 `BAAI/bge-small-zh-v1.5` 模型。

### 4.2 向量存储 (app/rag/vector_store.py)

```python
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings

_client = None

def get_chroma_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
    return _client

def get_job_collection():
    return get_chroma_client().get_or_create_collection(
        name=settings.CHROMA_COLLECTION_JOBS,
        metadata={"hnsw:space": "cosine"}
    )

def get_learning_collection():
    return get_chroma_client().get_or_create_collection(
        name=settings.CHROMA_COLLECTION_LEARNING,
        metadata={"hnsw:space": "cosine"}
    )
```

### 4.3 文档摄入 (app/rag/ingest_jobs.py + app/rag/ingest_learning.py)

```python
# ingest_jobs.py
async def ingest_all_jobs():
    """系统启动时从 MySQL 读取所有岗位，向量化存入 ChromaDB"""
    async with AsyncSessionLocal() as db:
        jobs = await db.execute(select(Job))
        for job in jobs:
            text = f"{job.job_title}\n{job.job_description}\n{job.requirements}"
            collection.add(
                ids=[str(job.id)],
                documents=[text],
                metadatas=[{
                    "job_title": job.job_title,
                    "company": job.company,
                    "industry": job.industry,
                    "salary_range": job.salary_range,
                }]
            )
```

### 4.4 三个检索器 (app/rag/retrievers.py)

```python
class JobRetriever:
    """岗位语义搜索 — 替代 SQL LIKE"""
    async def search(self, query: str, top_k: int = 10, filters: dict = None) -> list[JobResult]:
        results = collection.query(query_texts=[query], n_results=top_k, where=filters)
        return [JobResult(**m) for m in results]

class ResumeJobMatcher:
    """简历-岗位混合匹配 — 向量相似度 + LLM 维度打分"""
    async def match(self, resume_text: str, top_k: int = 20) -> list[MatchResult]:
        # Step 1: 向量检索召回 top_k 候选
        candidates = await job_retriever.search(resume_text, top_k)
        # Step 2: LLM 对每个候选做 7 维打分（复用 job_matcher agent）
        graph = build_job_matcher_graph()
        scores = await asyncio.gather(*[
            graph.ainvoke({"user_profile": profile, "job": c.job})
            for c in candidates
        ])
        return ranked_merge(candidates, scores)

class LearningRetriever:
    """学习资源检索 — 根据目标岗位/技能检索相关课程、文档、技术栈"""
    async def search_resources(self, target_job: str, skill_gaps: list[str], top_k: int = 10) -> list[Resource]:
        query = f"岗位: {target_job}\n需要学习的技能: {', '.join(skill_gaps)}"
        results = learning_collection.query(query_texts=[query], n_results=top_k)
        return [Resource(**m) for m in results]
```

### 4.5 RAG 集成到 Agent

修改受影响 Agent 的 LangGraph 节点：

- **job_matcher/graph.py** `match_jobs` 节点：前置增加 `retrieve_candidates` 节点 → 向量检索替代 SQL `LIKE` 模糊查询 + 混合打分
- **learning_plan/graph.py** `generate_plan` 节点：前置增加 `retrieve_resources` 节点 → 检索学习资源注入 LLM prompt
- **api/v1/jobs.py** `search` 端点：新增 `/jobs/search?q=Java开发` → 调用 `JobRetriever.search()`

---

## Phase 5: LangGraph Agent 重构

(与 Plan agent 方案一致，修改点标注 ★)

### 5.1 AgentBase ABC → 增加 Harness 接口

```python
class AgentBase(ABC):
    @abstractmethod
    def build_graph(self) -> StateGraph: ...
    @abstractmethod
    async def run(self, input_data: dict) -> dict: ...
    
    # ★新增 Harness 接口
    @property
    def max_retries(self) -> int: return 3
    @property
    def timeout_seconds(self) -> int: return 300
    @property
    def cacheable(self) -> bool: return True  # 是否缓存结果
```

### 5.2 5 个 Agent LangGraph 图结构

```
resume_analyzer (★合并 resume_extractor + data_analyzer):
  Phase 1 — 提取: [process_text] → [process_file] → [process_image] → [integrate_info]
  → [extract_params] → [check_completeness]
  → (缺失? → [generate_question] → 前端追问 → loop back to extract_params)
  Phase 2 — 分析: (完整✓) → [analyze_profile] → [generate_report] → END

job_matcher: ★ RAG 增强
  [load_user_profile] → [retrieve_candidates★] → [neo4j_enrich]
  → [llm_match_parallel] → [rank_results] → [save_report] → END

career_planner:
  [get_top_job] → [predict_trends] → [get_promotion_data]
  → [generate_career_path] → [plot_chart] → [save_plan] → END

learning_plan: ★ RAG 增强
  [load_profile] → [retrieve_resources★] → [generate_plan]
  → [polish_loop] → [save_plan] → END
  子图: daily_tasks, adjust_tasks, export_plan
```

### 5.3 统一注册表 → 升级为 Harness 注册

```python
# app/agents/registry.py → 集成到 harness.py
REGISTRY = {
    "resume_analyzer": ResumeAnalyzerAgent(),
    "job_matcher": JobMatcherAgent(),
    "career_planner": CareerPlannerAgent(),
    "learning_plan": LearningPlanAgent(),
}

def get_agent(agent_id: str) -> AgentBase:
    return REGISTRY[agent_id]
```

---

## Phase 6: FastAPI 应用 + 认证 + 中间件

### 6.1 main.py

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.error_handler import register_exception_handlers
from app.middleware.rate_limiter import RateLimitMiddleware
from app.rag.ingest_jobs import ingest_all_jobs  # ★启动摄入

async def lifespan(app):
    await ingest_all_jobs()           # ★启动时构建向量索引
    from app.agents.job_matcher.db_utils import init_neo4j_job_profiles
    init_neo4j_job_profiles()
    yield
    await neo4j_manager.close()
    await redis_pool.disconnect()

app = FastAPI(title="Career Service AI Platform", version="3.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
app.add_middleware(RateLimitMiddleware)  # ★Redis 限流
register_exception_handlers(app)

# Routers
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(agents.router, prefix="/api/v1/agents")
app.include_router(resume.router, prefix="/api/v1/resume")
# ... 所有 router
```

### 6.2 JWT 认证 → Redis 增强

同步流程：
- login → 生成 access_token (JWT, 1h) + refresh_token (UUID, 7d 存 Redis)
- logout → access_token 加入 Redis 黑名单 (TTL 对齐 JWT 过期时间) + refresh_token 删除
- 每次请求 → `verify_token` 先查 Redis 黑名单，再 decode JWT
- refresh → 验证 refresh_token (Redis 中存在) → 签发新 access_token + 轮换 refresh_token

### 6.3 限流中间件 (app/middleware/rate_limiter.py)

```python
class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        user_id = get_user_id_or_ip(request)
        key = f"rate_limit:{user_id}:{datetime.now().minute}"
        r = await get_redis()
        count = await r.incr(key)
        await r.expire(key, 60)
        if count > settings.REDIS_RATE_LIMIT:
            return JSONResponse(status_code=429, content={"error": "Too many requests"})
        return await call_next(request)
```

### 6.4 端点示例（含 Harness 调用）

```python
# api/v1/matching.py
@router.post("/match")
async def match_jobs(
    user: dict = Depends(get_current_user),
    harness: AgentHarness = Depends(get_harness),
):
    result = await harness.run("job_matcher", {
        "user_id": user["user_id"],
    })
    return {"success": True, "matches": result["matches"]}
```

所有 Agent 端点通过 `harness.run()` 或 `harness.run_async()` 调用，统一走缓存+重试+日志链路。

---

## Phase 7: 前端 API 对接

### 8.1 API Client 层 (src/api/)

```
src/api/
  client.js          # axios + JWT interceptor + 401 redirect
  auth.js            # login, register, logout, refresh
  jobs.js            # getJobs, getJobDetail, searchJobs
  resume.js          # extractResume, supplementResume
  analysis.js        # analyze
  matching.js        # match
  careerPlan.js      # getCareerPlan
  learningPlan.js    # generate, polish, dailyTasks, adjust, export
  favorites.js       # getFavorites, addFavorite, removeFavorite
```

### 8.2 Pinia Auth Store

```javascript
// src/stores/auth.js
export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    accessToken: localStorage.getItem('access_token'),
    refreshToken: localStorage.getItem('refresh_token'),
  }),
  getters: {
    isLoggedIn: (s) => !!s.accessToken,
  },
  actions: {
    async login(username, password) { ... },
    async logout() {
      await api.post('/auth/logout', { refresh_token: this.refreshToken })
      this.accessToken = null
      this.refreshToken = null
      localStorage.clear()
    },
    async refresh() { ... },
  }
})
```

### 8.3 页面改造清单

| 页面 | 改造内容 |
|------|---------|
| App.vue | `isLoggedIn` 改用 `useAuthStore` |
| Home.vue | hotJobs 换 API，userData 换 AuthStore，移除 3 重 onMounted |
| JobExplorer.vue | 14MB data.json 换 API 分页，过滤器真正生效 |
| JobDetail.vue | data.json 换 `getJobDetail(id)`，Neo4j 走后端代理，修 3 重 onMounted |
| Profile/Index.vue | 对话式简历提取接真实 API，雷达图数据实时更新 |
| PersonalInfo.vue | 所有数据来自 API，移除硬编码 |
| AIReport.vue | `aiReportData` mock 换 API，GeoJSON CDN 加 fallback |
| GrowthTracker.vue | 修 ElMessage import，任务数据接 API |
| FavoriteJobs.vue | localStorage 换 API，修 `/job-explorer` 为 `/jobs` |
| PolishAndExport.vue | 报告内容从 API 获取，AI 润色接真实端点 |

### 8.4 死代码清理

- 删除: `mock/data.js`, `assets/data.json`, `mock/promotion/`, `mock/promotionData.json`, `mockGraph.js`
- 删除: `stores/counter.js`, `components/CareerGraph.vue`
- 删除: `axios`, `echarts-wordcloud`, `vue-force-graph`, `mockjs` (未用依赖)

---

## Phase 8: 测试 + 最终验证

### 9.1 测试结构

```
tests/
  conftest.py               # async test client + test DB + mock Redis + test Chroma
  test_auth.py              # 注册/登录/刷新/登出
  test_resume.py            # 简历提取 + 追问
  test_matching.py          # 人岗匹配
  test_career_plan.py       # 职业规划
  test_learning_plan.py     # 学习计划
  test_rag.py               # 向量检索准确性
  test_harness.py           # AgentHarness 编排（缓存/重试/异步）
  test_rate_limiter.py      # 限流中间件
```

### 9.2 最终验证清单

**基础设施**:
- [ ] `curl localhost:8000/docs` OpenAPI 页面加载
- [ ] `curl localhost:8000/api/v1/health` 返回 200
- [ ] 限流中间件生效（60 req/min 返回 429）

**认证**:
- [ ] 注册 → 登录 → 拿到 token → 调用需要认证的接口
- [ ] 登出后 token 进黑名单 → 401
- [ ] Refresh token 轮换正常

**Agent + Harness**:
- [ ] 所有 5 个 Agent 通过 harness.run() 调用成功
- [ ] agent_runs 表有执行记录
- [ ] 缓存命中时第二调用不消耗 LLM API
- [ ] 异步任务队列正常（`harness.run_async()` → 轮询 → 拿到结果）

**RAG**:
- [ ] `/api/v1/jobs/search?q=Python后端` 返回语义相关岗位（非字面匹配）
- [ ] 人岗匹配结果包含向量相似度分数
- [ ] 学习计划生成包含检索到的学习资源

**前端**:
- [ ] `npm run dev` 正常启动
- [ ] Network 面板显示所有数据来自 API（无 data.json 加载）
- [ ] 3 个断路由修复
- [ ] ElMessage 运行时无错误
- [ ] 所有页面：空态/加载态/错误态正常展示

---

## 实施顺序

```
Phase 1: 项目骨架 + 配置 + DB 层 + Redis ─── 2 天
Phase 2: 11 项 Bug 修复                        ─── 1 天
Phase 3: Agent Harness 编排引擎                ─── 2 天  ★
Phase 4: RAG 知识库                            ─── 2 天  ★
Phase 5: 4 个 LangGraph Agent                  ─── 3 天
Phase 6: FastAPI + JWT + 中间件 + 端点         ─── 2 天
Phase 7: 前端 API 对接 + 死代码清理            ─── 3 天
Phase 8: 测试 + 验证                           ─── 2 天
                                      ──────────────
                                       总计 ~17 天
```

Phase 3-4 可并行，Phase 5 可与 Phase 6 部分并行。Phase 8 需等 Phase 5-6 完成后启动。

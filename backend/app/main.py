from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.neo4j import neo4j_manager
from app.db.redis import close_redis, get_redis_pool
from app.middleware.error_handler import register_exception_handlers
from app.middleware.rate_limiter import RateLimitMiddleware

# API routers
from app.api.v1 import (
    auth, agents, resume, matching, career_plan, learning_plan, jobs, favorites,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: init Redis pool
    await get_redis_pool()

    # Startup: register all agents with Harness
    from app.agents.registry import init_agents
    init_agents()

    # Startup: ingest RAG data (non-blocking — runs in background)
    import asyncio as _asyncio
    _asyncio.create_task(_ingest_rag_data())

    yield

    # Shutdown
    await neo4j_manager.close()
    await close_redis()


async def _ingest_rag_data():
    """Background task: build vector indexes on startup."""
    try:
        from app.rag.ingest_jobs import ingest_all_jobs
        await ingest_all_jobs()
    except Exception:
        pass
    try:
        from app.rag.ingest_learning import ingest_learning_resources
        await ingest_learning_resources()
    except Exception:
        pass


app = FastAPI(
    title="Career Service AI Platform",
    version="3.0.0",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)

register_exception_handlers(app)

# Register API routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["Agents"])
app.include_router(resume.router, prefix="/api/v1/resume", tags=["Resume"])
app.include_router(matching.router, prefix="/api/v1/matching", tags=["Matching"])
app.include_router(career_plan.router, prefix="/api/v1/career-plan", tags=["Career Plan"])
app.include_router(learning_plan.router, prefix="/api/v1/learning-plan", tags=["Learning Plan"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["Jobs"])
app.include_router(favorites.router, prefix="/api/v1/favorites", tags=["Favorites"])


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "3.0.0"}

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.neo4j import neo4j_manager
from app.db.redis import close_redis, get_redis_pool
from app.middleware.error_handler import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await get_redis_pool()
    yield
    # Shutdown
    await neo4j_manager.close()
    await close_redis()


app = FastAPI(
    title="Career Service AI Platform",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "3.0.0"}

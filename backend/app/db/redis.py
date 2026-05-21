from app.config import settings

# When running locally with SQLite, use in-memory store instead of Redis
if settings.DB_BACKEND == "sqlite":
    from app.db.memory_store import (  # noqa: F401
        get_redis_pool,
        get_redis,
        close_redis,
        blacklist_token,
        is_token_blacklisted,
        check_rate_limit,
        cache_agent_result,
        get_cached_agent_result,
        store_refresh_token,
        get_refresh_user,
        revoke_refresh_token,
    )
else:
    import redis.asyncio as aioredis

    _pool: aioredis.ConnectionPool | None = None

    async def get_redis_pool() -> aioredis.ConnectionPool:
        global _pool
        if _pool is None:
            _pool = aioredis.ConnectionPool.from_url(
                settings.REDIS_URL, max_connections=20, decode_responses=True
            )
        return _pool

    async def get_redis() -> aioredis.Redis:
        pool = await get_redis_pool()
        return aioredis.Redis(connection_pool=pool)

    async def close_redis():
        global _pool
        if _pool:
            await _pool.disconnect()
            _pool = None

    # --- Token blacklist ---

    async def blacklist_token(token: str, expire_seconds: int):
        r = await get_redis()
        await r.setex(f"blacklist:{token}", expire_seconds, "1")

    async def is_token_blacklisted(token: str) -> bool:
        r = await get_redis()
        return await r.exists(f"blacklist:{token}") > 0

    # --- Rate limiter ---

    async def check_rate_limit(user_key: str, limit: int, window: int = 60) -> bool:
        r = await get_redis()
        current = await r.incr(f"rate:{user_key}")
        if current == 1:
            await r.expire(f"rate:{user_key}", window)
        return current <= limit

    # --- Agent result cache ---

    async def cache_agent_result(agent_id: str, input_hash: str, value: str, ttl: int = 3600):
        r = await get_redis()
        await r.setex(f"agent_cache:{agent_id}:{input_hash}", ttl, value)

    async def get_cached_agent_result(agent_id: str, input_hash: str) -> str | None:
        r = await get_redis()
        return await r.get(f"agent_cache:{agent_id}:{input_hash}")

    # --- Refresh token store ---

    async def store_refresh_token(user_id: int, token: str, days: int = 7):
        r = await get_redis()
        await r.setex(f"refresh:{token}", days * 86400, str(user_id))

    async def get_refresh_user(token: str) -> int | None:
        r = await get_redis()
        uid = await r.get(f"refresh:{token}")
        return int(uid) if uid else None

    async def revoke_refresh_token(token: str):
        r = await get_redis()
        await r.delete(f"refresh:{token}")

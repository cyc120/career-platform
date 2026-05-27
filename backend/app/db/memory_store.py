"""In-memory drop-in replacement for Redis when Redis is unavailable.

Provides the same async function signatures as redis.py using Python dicts.
"""
import time
from typing import Any

_store: dict[str, tuple[Any, float | None]] = {}  # key -> (value, expire_ts or None)
_counters: dict[str, tuple[int, float]] = {}       # key -> (count, expire_ts)


def _is_expired(expire_ts: float | None) -> bool:
    return expire_ts is not None and time.time() > expire_ts


def _get(key: str) -> Any | None:
    entry = _store.get(key)
    if entry is None:
        return None
    value, expire_ts = entry
    if _is_expired(expire_ts):
        del _store[key]
        return None
    return value


def _set(key: str, value: Any, ttl: int | None = None):
    expire_ts = time.time() + ttl if ttl else None
    _store[key] = (value, expire_ts)


def _delete(key: str):
    _store.pop(key, None)


# --- Connection (no-ops for compatibility) ---

async def get_redis_pool():
    return None


async def get_redis():
    return None


async def close_redis():
    _store.clear()
    _counters.clear()


# --- Token blacklist ---

async def blacklist_token(token: str, expire_seconds: int):
    _set(f"blacklist:{token}", "1", expire_seconds)


async def is_token_blacklisted(token: str) -> bool:
    return _get(f"blacklist:{token}") is not None


# --- Rate limiter ---

async def check_rate_limit(user_key: str, limit: int, window: int = 60) -> bool:
    now = time.time()
    key = f"rate:{user_key}"
    entry = _counters.get(key)

    if entry is None or now > entry[1]:
        _counters[key] = (1, now + window)
        return True

    count, expire_ts = entry
    count += 1
    _counters[key] = (count, expire_ts)
    return count <= limit


# --- Agent result cache ---

async def cache_agent_result(agent_id: str, input_hash: str, value: str, ttl: int = 3600):
    _set(f"agent_cache:{agent_id}:{input_hash}", value, ttl)


async def get_cached_agent_result(agent_id: str, input_hash: str) -> str | None:
    return _get(f"agent_cache:{agent_id}:{input_hash}")


# --- Refresh token store ---

async def store_refresh_token(user_id: int, token: str, days: int = 7):
    _set(f"refresh:{token}", str(user_id), days * 86400)


async def get_refresh_user(token: str) -> int | None:
    uid = _get(f"refresh:{token}")
    return int(uid) if uid else None


async def revoke_refresh_token(token: str):
    _delete(f"refresh:{token}")

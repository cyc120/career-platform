from datetime import datetime
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings
from app.db.redis import check_rate_limit


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Get client identifier
        user_id = request.headers.get("x-user-id", request.client.host)

        # Only rate-limit API routes
        if not request.url.path.startswith("/api"):
            return await call_next(request)

        key = f"{user_id}:{datetime.utcnow().minute}"
        allowed = await check_rate_limit(key, settings.REDIS_RATE_LIMIT)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"success": False, "error": "Rate limit exceeded. Try again later."},
            )

        return await call_next(request)

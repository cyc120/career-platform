from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.security import decode_access_token
from app.db.redis import is_token_blacklisted

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    token = credentials.credentials

    try:
        if await is_token_blacklisted(token):
            raise HTTPException(status_code=401, detail="Token revoked")
    except Exception:
        pass  # Redis unavailable — allow request

    try:
        user_id = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return {"user_id": user_id}

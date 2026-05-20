from fastapi import APIRouter, Depends
from app.agents.harness import harness
from app.middleware.auth import get_current_user

router = APIRouter()


@router.post("/match")
async def match_jobs(user: dict = Depends(get_current_user)):
    result = await harness.run(
        "job_matcher",
        {"user_id": user["user_id"]},
        user_id=user["user_id"],
    )
    return result

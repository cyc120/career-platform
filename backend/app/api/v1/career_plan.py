from fastapi import APIRouter, Depends
from app.agents.harness import harness
from app.middleware.auth import get_current_user

router = APIRouter()


@router.post("")
async def run_career_plan(user: dict = Depends(get_current_user)):
    result = await harness.run(
        "career_planner",
        {"user_id": user["user_id"]},
        user_id=user["user_id"],
    )
    return result

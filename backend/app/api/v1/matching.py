from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict
from app.agents.harness import harness
from app.middleware.auth import get_current_user

router = APIRouter()


class MatchRequest(BaseModel):
    radar_data: Optional[List[int]] = None
    dimension_details: Optional[Dict] = None


@router.post("/match")
async def match_jobs(req: MatchRequest = None, user: dict = Depends(get_current_user)):
    input_data = {"user_id": user["user_id"]}

    # If frontend sends profile data, use it directly
    if req and req.radar_data and any(v > 0 for v in req.radar_data):
        input_data["user_profile"] = {
            "radar_data": req.radar_data,
            "dimension_details": req.dimension_details or {},
            "source": "frontend",
        }

    result = await harness.run(
        "job_matcher",
        input_data,
        user_id=user["user_id"],
    )
    return result

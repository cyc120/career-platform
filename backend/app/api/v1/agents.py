from fastapi import APIRouter, Depends
from app.agents.harness import harness
from app.middleware.auth import get_current_user

router = APIRouter()


@router.get("")
async def list_agents(user: dict = Depends(get_current_user)):
    return {"success": True, "agents": harness.list_agents()}

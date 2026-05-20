from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from app.db.mysql import get_db
from app.middleware.auth import get_current_user

router = APIRouter()


class FavoriteRequest(BaseModel):
    job_id: int


@router.get("")
async def list_favorites(user: dict = Depends(get_current_user), db=Depends(get_db)):
    result = await db.execute(
        text(
            "SELECT f.id, f.job_id, j.job_title, j.company, j.industry, j.city, "
            "j.salary_range, f.created_at "
            "FROM favorites f JOIN jobs j ON f.job_id = j.id "
            "WHERE f.user_id = :uid ORDER BY f.created_at DESC"
        ),
        {"uid": user["user_id"]},
    )
    return {"success": True, "favorites": [dict(r._mapping) for r in result.fetchall()]}


@router.post("")
async def add_favorite(req: FavoriteRequest, user: dict = Depends(get_current_user), db=Depends(get_db)):
    try:
        await db.execute(
            text("INSERT INTO favorites (user_id, job_id) VALUES (:uid, :jid)"),
            {"uid": user["user_id"], "jid": req.job_id},
        )
        await db.commit()
    except Exception:
        raise HTTPException(400, "Already favorited or job not found")
    return {"success": True}


@router.delete("/{job_id}")
async def remove_favorite(job_id: int, user: dict = Depends(get_current_user), db=Depends(get_db)):
    await db.execute(
        text("DELETE FROM favorites WHERE user_id = :uid AND job_id = :jid"),
        {"uid": user["user_id"], "jid": job_id},
    )
    await db.commit()
    return {"success": True}

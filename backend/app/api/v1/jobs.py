from fastapi import APIRouter, Query, Depends
from sqlalchemy import text
from app.db.mysql import get_db
from app.rag.retrievers import job_retriever

router = APIRouter()


@router.get("")
async def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, le=100),
    keyword: str = Query(""),
    industry: str = Query(""),
    city: str = Query(""),
    db=Depends(get_db),
):
    """List jobs with optional keyword filtering. Uses RAG for keyword searches."""
    if keyword:
        results = job_retriever.search(keyword, top_k=page_size, industry=industry or None, city=city or None)
        return {
            "success": True,
            "jobs": [
                {"id": int(r.id), "job_title": r.job_title, "company": r.company,
                 "industry": r.industry, "city": r.city, "salary_range": r.salary_range,
                 "score": r.score}
                for r in results
            ],
            "source": "vector",
        }

    offset = (page - 1) * page_size
    query = "SELECT id, job_title, company, industry, city, salary_range, publish_date FROM jobs WHERE 1=1"
    params = {}
    if industry:
        query += " AND industry = :ind"
        params["ind"] = industry
    if city:
        query += " AND city = :ct"
        params["ct"] = city
    query += " ORDER BY publish_date DESC LIMIT :lim OFFSET :off"
    params["lim"] = page_size
    params["off"] = offset

    result = await db.execute(text(query), params)
    jobs = [dict(r._mapping) for r in result.fetchall()]
    return {"success": True, "jobs": jobs, "source": "sql"}


@router.get("/search")
async def search_jobs(q: str = Query(""), top_k: int = Query(10)):
    """Semantic job search via RAG."""
    results = job_retriever.search(q, top_k=top_k)
    return {
        "success": True,
        "jobs": [
            {"id": int(r.id), "job_title": r.job_title, "company": r.company,
             "industry": r.industry, "city": r.city, "salary_range": r.salary_range,
             "score": r.score}
            for r in results
        ],
    }


@router.get("/hot")
async def hot_jobs(db=Depends(get_db)):
    """Top 10 most recent jobs."""
    result = await db.execute(
        text("SELECT id, job_title, company, industry, city, salary_range FROM jobs ORDER BY publish_date DESC LIMIT 10")
    )
    return {"success": True, "jobs": [dict(r._mapping) for r in result.fetchall()]}


@router.get("/{job_id}")
async def get_job_detail(job_id: int, db=Depends(get_db)):
    result = await db.execute(
        text("SELECT * FROM jobs WHERE id = :jid"), {"jid": job_id}
    )
    row = result.fetchone()
    if not row:
        return {"success": False, "error": "Job not found"}
    return {"success": True, "job": dict(row._mapping)}

"""Ingest all jobs from MySQL into ChromaDB vector store.

Called at system startup (FastAPI lifespan) to keep vector index in sync.
"""
from sqlalchemy import text
from app.db.mysql import AsyncSessionLocal
from app.rag.embedding import get_embeddings
from app.rag.vector_store import get_job_collection


async def ingest_all_jobs():
    """Read all jobs from MySQL and upsert into ChromaDB."""
    embeddings = get_embeddings()
    collection = get_job_collection()

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text(
                "SELECT id, job_title, company, industry, city, salary_range, "
                "job_description, requirements FROM jobs"
            )
        )
        rows = result.fetchall()

    if not rows:
        return

    ids = [str(r[0]) for r in rows]
    documents = []
    metadatas = []

    for r in rows:
        text_parts = [r[1] or "", r[6] or "", r[7] or ""]
        documents.append("\n".join(text_parts))
        metadatas.append({
            "job_title": r[1] or "",
            "company": r[2] or "",
            "industry": r[3] or "",
            "city": r[4] or "",
            "salary_range": r[5] or "",
        })

    # Compute embeddings and upsert
    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
    )

    print(f"[RAG] Ingested {len(rows)} jobs into ChromaDB.")


async def ingest_single_job(job_id: int, job_title: str, job_description: str,
                              requirements: str, **meta):
    """Add or update a single job in the vector index."""
    collection = get_job_collection()
    text = f"{job_title}\n{job_description}\n{requirements}"
    collection.upsert(
        ids=[str(job_id)],
        documents=[text],
        metadatas=[{k: v or "" for k, v in meta.items()}],
    )

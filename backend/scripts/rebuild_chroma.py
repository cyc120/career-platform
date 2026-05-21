"""Rebuild ChromaDB vector index with all jobs from SQLite."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import asyncio
from app.rag.vector_store import reset_collections, get_job_collection
from app.rag.embedding import get_embeddings
from app.db.mysql import AsyncSessionLocal
from sqlalchemy import text


async def rebuild():
    print("Resetting ChromaDB collections...")
    reset_collections()

    collection = get_job_collection()
    embeddings = get_embeddings()

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text(
                "SELECT id, job_title, company, industry, city, salary_range, "
                "job_description, requirements, company_scale FROM jobs"
            )
        )
        rows = result.fetchall()

    print(f"Found {len(rows)} jobs in database.")

    if not rows:
        print("No jobs found. Aborting.")
        return

    batch_size = 200
    for start in range(0, len(rows), batch_size):
        batch = rows[start:start + batch_size]

        ids = [str(r[0]) for r in batch]
        documents = []
        metadatas = []

        for r in batch:
            text_parts = [r[1] or "", r[6] or "", r[7] or ""]
            documents.append("\n".join(text_parts))
            metadatas.append({
                "job_title": r[1] or "",
                "company": r[2] or "",
                "industry": r[3] or "",
                "city": r[4] or "",
                "salary_range": r[5] or "",
                "company_scale": r[8] or "",
            })

        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )
        print(f"  Batch {start // batch_size + 1}: ingested {len(batch)} jobs")

    print(f"Done. ChromaDB now has {collection.count()} documents.")


if __name__ == "__main__":
    asyncio.run(rebuild())

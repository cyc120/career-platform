"""Three retrievers for the RAG system:
1. JobRetriever — semantic job search
2. ResumeJobMatcher — resume-to-job vector + LLM hybrid matching
3. LearningRetriever — learning resource search
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.rag.embedding import get_embeddings
from app.rag.vector_store import get_job_collection, get_learning_collection


@dataclass
class JobResult:
    id: str
    job_title: str
    company: str
    industry: str
    city: str
    salary_range: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceResult:
    id: str
    title: str
    category: str
    level: str
    duration: str
    source: str
    score: float


class JobRetriever:
    """Semantic job search using vector similarity.

    Replaces the old SQL LIKE-based fuzzy search with embedding-based
    semantic matching for better recall and relevance.
    """

    def search(
        self,
        query: str,
        top_k: int = 10,
        industry: str = None,
        city: str = None,
    ) -> List[JobResult]:
        collection = get_job_collection()
        where_filter = {}
        if industry:
            where_filter["industry"] = industry
        if city:
            where_filter["city"] = city

        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_filter if where_filter else None,
        )

        jobs = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                dist = results["distances"][0][i] if results["distances"] else 0
                score = max(0.0, 1.0 - dist)  # cosine distance → similarity

                jobs.append(JobResult(
                    id=doc_id,
                    job_title=meta.get("job_title", ""),
                    company=meta.get("company", ""),
                    industry=meta.get("industry", ""),
                    city=meta.get("city", ""),
                    salary_range=meta.get("salary_range", ""),
                    score=round(score, 4),
                ))

        return sorted(jobs, key=lambda j: j.score, reverse=True)


class ResumeJobMatcher:
    """Resume-to-job hybrid matching.

    Phase 1: Vector retrieval to get top-N candidate jobs.
    Phase 2: LLM-based 7-dimension scoring for each candidate.
    """

    def retrieve_candidates(self, resume_text: str, top_k: int = 20) -> list[str]:
        """Vector-only first pass: get top-k candidate job IDs."""
        collection = get_job_collection()
        results = collection.query(query_texts=[resume_text], n_results=top_k)
        if results["ids"] and results["ids"][0]:
            return results["ids"][0]
        return []

    def get_job_texts(self, job_ids: list[str]) -> dict[str, str]:
        """Get job document texts for a list of IDs."""
        collection = get_job_collection()
        results = collection.get(ids=job_ids)
        texts = {}
        if results["ids"]:
            for i, doc_id in enumerate(results["ids"]):
                texts[doc_id] = results["documents"][i] if results["documents"] else ""
        return texts


class LearningRetriever:
    """Learning resource search for the learning plan agent.

    Given a target job and skill gaps, finds relevant courses,
    tutorials, and documentation to recommend.
    """

    def search(self, target_job: str, skill_gaps: list[str], top_k: int = 5) -> List[ResourceResult]:
        collection = get_learning_collection()

        query = f"{target_job} {' '.join(skill_gaps)}"
        results = collection.query(query_texts=[query], n_results=top_k)

        resources = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                dist = results["distances"][0][i] if results["distances"] else 0
                score = max(0.0, 1.0 - dist)

                resources.append(ResourceResult(
                    id=doc_id,
                    title=meta.get("title", ""),
                    category=meta.get("category", ""),
                    level=meta.get("level", ""),
                    duration=meta.get("duration", ""),
                    source=meta.get("source", ""),
                    score=round(score, 4),
                ))

        return sorted(resources, key=lambda r: r.score, reverse=True)


# Singleton instances
job_retriever = JobRetriever()
resume_job_matcher = ResumeJobMatcher()
learning_retriever = LearningRetriever()

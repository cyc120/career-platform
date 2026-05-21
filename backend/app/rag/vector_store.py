import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings

_client: chromadb.ClientAPI | None = None


def get_chroma_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


def get_job_collection():
    """Collection for job descriptions — semantic search over job listings."""
    return get_chroma_client().get_or_create_collection(
        name=settings.CHROMA_COLLECTION_JOBS,
        metadata={"hnsw:space": "cosine"},
    )


def get_learning_collection():
    """Collection for learning resources — knowledge base for learning plan agent."""
    return get_chroma_client().get_or_create_collection(
        name=settings.CHROMA_COLLECTION_LEARNING,
        metadata={"hnsw:space": "cosine"},
    )


def reset_collections():
    """Drop and recreate all collections. Use with caution."""
    client = get_chroma_client()
    for name in [settings.CHROMA_COLLECTION_JOBS, settings.CHROMA_COLLECTION_LEARNING]:
        try:
            client.delete_collection(name)
        except Exception:
            pass
    global _client
    _client = None

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM
    OPENAI_API_KEY: str
    OPENAI_BASE_URL: str = "https://api.deepseek.com/v1"
    OPENAI_MODEL: str = "deepseek-chat"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-ada-002"

    # Database backend: "sqlite" (local) or "mysql"
    DB_BACKEND: str = "sqlite"

    # MySQL (only used when DB_BACKEND="mysql")
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "root"
    MYSQL_DATABASE: str = "career_platform"

    # Neo4j (optional — gracefully skipped if unavailable)
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "neo4jpassword"

    # Redis (only used when DB_BACKEND="mysql"; otherwise in-memory)
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600
    REDIS_RATE_LIMIT: int = 60

    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./chroma_data"
    CHROMA_COLLECTION_JOBS: str = "job_descriptions"
    CHROMA_COLLECTION_LEARNING: str = "learning_resources"

    # JWT
    JWT_SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Harness
    AGENT_MAX_RETRIES: int = 3
    AGENT_TIMEOUT_SECONDS: int = 300
    AGENT_ASYNC_WORKERS: int = 4

    # Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 16

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

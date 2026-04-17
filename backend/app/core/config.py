from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_ENV: str = "development"
    APP_NAME: str = "AI Research Assistant"
    APP_VERSION: str = "1.0.0"
    BACKEND_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"

    # Claude AI
    ANTHROPIC_API_KEY: str = ""
    # Model selection — Claude Sonnet 4.5 is the current Sonnet flagship with
    # materially better academic writing than Sonnet 4. For absolute-best
    # results set to "claude-opus-4-5" (≈2× cost). Sonnet 4.6 is the latest.
    CLAUDE_MODEL: str = "claude-sonnet-4-5"
    CLAUDE_MAX_TOKENS: int = 16000
    CLAUDE_TEMPERATURE: float = 0.3
    # Prompt caching — cached blocks cost 10% of input tokens on reads.
    # With 7 sequential calls sharing ctx_str, caching typically saves 60-70%
    # on input costs, roughly paying for the Sonnet-4.5 upgrade.
    CLAUDE_USE_PROMPT_CACHING: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/research_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "change-me-in-production-minimum-32-characters"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Vector Store
    VECTOR_STORE: str = "faiss"
    FAISS_INDEX_PATH: str = "./faiss_indexes"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    PINECONE_API_KEY: str = ""
    PINECONE_ENVIRONMENT: str = ""
    PINECONE_INDEX: str = "research-papers"

    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 50

    # Agent
    AGENT_MAX_RETRIES: int = 3
    AGENT_RETRY_DELAY: float = 1.0
    MAX_CONTEXT_TOKENS: int = 50000
    EPISODIC_MEMORY_WINDOW: int = 20

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
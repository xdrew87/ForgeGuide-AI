from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = "postgresql://forgeguide:forgeguide@localhost:5432/forgeguide"

    # ── Qdrant ────────────────────────────────────────────────────────────────
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "forgeguide_chunks"

    # ── LLM provider ─────────────────────────────────────────────────────────
    # Options: anthropic | openai | ollama
    llm_provider: str = "anthropic"
    llm_model: str = "claude-sonnet-4-6"

    # Anthropic
    anthropic_api_key: str = ""

    # OpenAI
    openai_api_key: str = ""

    # Ollama
    ollama_base_url: str = "http://ollama:11434"   # docker-compose default
    ollama_vision_model: str = ""                  # e.g. llava, moondream
                                                   # blank = use llm_model

    # ── Embeddings ────────────────────────────────────────────────────────────
    # Options: anthropic (Voyage) | openai | ollama
    embedding_provider: str = "anthropic"
    embedding_model: str = "voyage-3-lite"
    embedding_dim: int = 1024   # voyage-3-lite=1024, openai ada=1536, nomic=768

    # ── Upload ────────────────────────────────────────────────────────────────
    max_upload_size_mb: int = 50
    allowed_extensions: str = "pdf"
    upload_dir: str = "/app/uploads"

    # ── App ───────────────────────────────────────────────────────────────────
    debug: bool = False
    log_level: str = "INFO"
    secret_key: str = "change-this-in-production"

    # Evidence threshold — answers below this are declined
    evidence_confidence_threshold: float = 0.45

    model_config = {"env_file": ".env", "case_sensitive": False}


@lru_cache
def get_settings() -> Settings:
    return Settings()

import os
import pytest

# Set env vars before any app imports so settings are correct
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("QDRANT_HOST", "localhost")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("LLM_PROVIDER", "anthropic")
os.environ.setdefault("EMBEDDING_PROVIDER", "anthropic")

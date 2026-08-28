"""
Provider-agnostic embedding service.
Supports: anthropic (Voyage AI), openai, ollama
"""
import logging
import httpx
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Ollama embed batch size — local models are slower, keep batches small
OLLAMA_BATCH_SIZE = 8


class EmbeddingService:
    def __init__(self):
        self.provider = settings.embedding_provider
        self.model = settings.embedding_model
        self.dim = settings.embedding_dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self.provider == "anthropic":
            return self._embed_voyage(texts)
        elif self.provider == "openai":
            return self._embed_openai(texts)
        elif self.provider == "ollama":
            return self._embed_ollama(texts)
        else:
            raise ValueError(f"Unknown embedding provider: {self.provider}")

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]

    # ── Anthropic / Voyage ────────────────────────────────────────────────────

    def _embed_voyage(self, texts: list[str]) -> list[list[float]]:
        """Voyage AI embeddings (Anthropic's recommended embedding partner).
        Voyage issues its own API keys, separate from the Anthropic API key —
        get one at https://dash.voyageai.com."""
        headers = {
            "Authorization": f"Bearer {settings.voyage_api_key}",
            "Content-Type": "application/json",
        }
        response = httpx.post(
            "https://api.voyageai.com/v1/embeddings",
            json={"input": texts, "model": self.model},
            headers=headers,
            timeout=60,
        )
        response.raise_for_status()
        return [item["embedding"] for item in response.json()["data"]]

    # ── OpenAI ────────────────────────────────────────────────────────────────

    def _embed_openai(self, texts: list[str]) -> list[list[float]]:
        import openai
        client = openai.OpenAI(api_key=settings.openai_api_key)
        response = client.embeddings.create(input=texts, model=self.model)
        return [item.embedding for item in response.data]

    # ── Ollama ────────────────────────────────────────────────────────────────

    def _embed_ollama(self, texts: list[str]) -> list[list[float]]:
        """
        Ollama /api/embed endpoint (Ollama >= 0.1.26).
        Falls back to /api/embeddings (single-text) for older versions.
        Batches to avoid overwhelming local GPU/CPU.
        """
        base_url = settings.ollama_base_url.rstrip("/")
        all_vectors: list[list[float]] = []

        for i in range(0, len(texts), OLLAMA_BATCH_SIZE):
            batch = texts[i : i + OLLAMA_BATCH_SIZE]
            vectors = self._ollama_batch(base_url, batch)
            all_vectors.extend(vectors)

        return all_vectors

    def _ollama_batch(self, base_url: str, texts: list[str]) -> list[list[float]]:
        # Try new batch endpoint first
        try:
            r = httpx.post(
                f"{base_url}/api/embed",
                json={"model": self.model, "input": texts},
                timeout=120,
            )
            if r.status_code == 200:
                data = r.json()
                # New API returns {"embeddings": [[...], ...]}
                if "embeddings" in data:
                    return data["embeddings"]
        except Exception:
            pass

        # Fall back: call single-text endpoint for each
        vectors = []
        for text in texts:
            r = httpx.post(
                f"{base_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
                timeout=60,
            )
            r.raise_for_status()
            vectors.append(r.json()["embedding"])
        return vectors


_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service

"""
Qdrant vector store — manages collection, upsert, and search.
"""
import logging
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue, FilterSelector
)
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class VectorStore:
    def __init__(self):
        self.client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
        self.collection = settings.qdrant_collection
        self.dim = settings.embedding_dim
        self._ensure_collection()

    def _ensure_collection(self):
        existing = {c.name for c in self.client.get_collections().collections}
        if self.collection not in existing:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=self.dim, distance=Distance.COSINE),
            )
            logger.info(f"Created Qdrant collection: {self.collection} (dim={self.dim})")
        else:
            # Verify dimension matches — catches provider switch without clean volumes
            info = self.client.get_collection(self.collection)
            existing_dim = info.config.params.vectors.size
            if existing_dim != self.dim:
                raise RuntimeError(
                    f"Qdrant collection has dimension {existing_dim} "
                    f"but EMBEDDING_DIM={self.dim}. "
                    f"Run: make clean && make up  to reset volumes when switching providers."
                )

    def upsert_chunks(self, chunks: list[dict]) -> list[str]:
        """
        chunks: list of dicts with keys:
          - chunk_id (str)
          - vector (list[float])
          - document_id (str)
          - document_title (str)
          - equipment_id (str | None)
          - page (int)
          - section (str | None)
          - text (str)
        Returns list of point IDs upserted.
        """
        points = []
        for c in chunks:
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, c["chunk_id"]))
            points.append(PointStruct(
                id=point_id,
                vector=c["vector"],
                payload={
                    "chunk_id": c["chunk_id"],
                    "document_id": c["document_id"],
                    "document_title": c.get("document_title", ""),
                    "equipment_id": c.get("equipment_id"),
                    "page": c["page"],
                    "section": c.get("section"),
                    "text": c["text"],
                },
            ))

        self.client.upsert(collection_name=self.collection, points=points)
        return [p.id for p in points]

    def search(
        self,
        query_vector: list[float],
        top_k: int = 8,
        equipment_id: str | None = None,
        score_threshold: float = 0.3,
    ) -> list[dict]:
        """
        Semantic search with optional equipment filter.
        Returns list of result dicts with score + payload.
        """
        filt = None
        if equipment_id:
            filt = Filter(
                must=[FieldCondition(key="equipment_id", match=MatchValue(value=equipment_id))]
            )

        results = self.client.search(
            collection_name=self.collection,
            query_vector=query_vector,
            limit=top_k,
            query_filter=filt,
            score_threshold=score_threshold,
            with_payload=True,
        )

        return [
            {
                "score": r.score,
                "chunk_id": r.payload.get("chunk_id"),
                "document_id": r.payload.get("document_id"),
                "document_title": r.payload.get("document_title"),
                "equipment_id": r.payload.get("equipment_id"),
                "page": r.payload.get("page"),
                "section": r.payload.get("section"),
                "text": r.payload.get("text"),
            }
            for r in results
        ]

    def delete_by_document(self, document_id: str):
        """Remove all vectors for a given document."""
        self.client.delete(
            collection_name=self.collection,
            points_selector=FilterSelector(
                filter=Filter(
                    must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
                )
            ),
        )


_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store

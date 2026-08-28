"""
Hybrid retrieval: semantic (Qdrant) + keyword (SQL LIKE) → RRF fusion.
"""
import logging
import re
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import get_settings
from app.models.models import DocumentChunk
from app.services.embedding import get_embedding_service
from app.services.vector_store import get_vector_store

logger = logging.getLogger(__name__)
settings = get_settings()

TOP_K_SEMANTIC = 10
TOP_K_KEYWORD = 6
RRF_K = 60  # RRF rank fusion constant


def _keyword_search(db: Session, query: str, equipment_id: str | None, top_k: int) -> list[dict]:
    """Simple keyword search using SQL ILIKE against chunk text."""
    keywords = [w for w in re.findall(r"\b\w{3,}\b", query.lower()) if len(w) > 2]
    if not keywords:
        return []

    # Build OR conditions for each keyword
    conditions = " OR ".join([f"LOWER(dc.text) LIKE :kw{i}" for i in range(len(keywords))])
    params = {f"kw{i}": f"%{kw}%" for i, kw in enumerate(keywords)}

    eq_filter = ""
    if equipment_id:
        eq_filter = "AND d.equipment_id = :equipment_id"
        params["equipment_id"] = equipment_id

    sql = text(f"""
        SELECT dc.id, dc.document_id, dc.page, dc.section, dc.text, dc.char_count,
               d.title as document_title, d.equipment_id
        FROM document_chunks dc
        JOIN documents d ON d.id = dc.document_id
        WHERE ({conditions}) {eq_filter}
        ORDER BY LENGTH(dc.text) DESC
        LIMIT :top_k
    """)
    params["top_k"] = top_k

    rows = db.execute(sql, params).fetchall()
    return [
        {
            "chunk_id": row.id,
            "document_id": row.document_id,
            "document_title": row.document_title,
            "equipment_id": row.equipment_id,
            "page": row.page,
            "section": row.section,
            "text": row.text,
            "score": None,  # no score for keyword
        }
        for row in rows
    ]


def _rrf_fuse(semantic: list[dict], keyword: list[dict]) -> list[dict]:
    """
    Reciprocal Rank Fusion to merge two ranked lists.
    Returns merged list sorted by fused score descending.
    """
    scores: dict[str, float] = {}
    sources: dict[str, dict] = {}

    for rank, item in enumerate(semantic):
        cid = item["chunk_id"]
        scores[cid] = scores.get(cid, 0) + 1 / (RRF_K + rank + 1)
        sources[cid] = item

    for rank, item in enumerate(keyword):
        cid = item["chunk_id"]
        scores[cid] = scores.get(cid, 0) + 1 / (RRF_K + rank + 1)
        sources[cid] = {**item, "score": item.get("score") or 0}

    merged = []
    for cid, fused_score in sorted(scores.items(), key=lambda x: -x[1]):
        entry = dict(sources[cid])
        entry["fused_score"] = round(fused_score, 4)
        merged.append(entry)

    return merged


def retrieve(
    db: Session,
    query: str,
    equipment_id: str | None = None,
    top_k: int = 6,
) -> list[dict]:
    """
    Hybrid retrieval pipeline.
    Returns top-k chunks ranked by RRF, each with metadata.
    """
    embedding_svc = get_embedding_service()
    vector_store = get_vector_store()

    # Semantic
    qvec = embedding_svc.embed_one(query)
    semantic_results = vector_store.search(
        query_vector=qvec,
        top_k=TOP_K_SEMANTIC,
        equipment_id=equipment_id,
        score_threshold=0.2,
    )

    # Keyword
    keyword_results = _keyword_search(db, query, equipment_id, TOP_K_KEYWORD)

    # Fuse
    merged = _rrf_fuse(semantic_results, keyword_results)

    return merged[:top_k]

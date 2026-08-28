"""
Document ingestion: PDF → text extraction → chunking → embedding → Qdrant.
OCR fallback for scanned/image-heavy PDFs.
"""
import logging
import os
import re
import tempfile
from pathlib import Path
from typing import Optional

import pymupdf as fitz  # PyMuPDF
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.models import Document, DocumentChunk, IngestionStatus
from app.services.embedding import get_embedding_service
from app.services.vector_store import get_vector_store

logger = logging.getLogger(__name__)
settings = get_settings()

CHUNK_SIZE = 800       # target chars per chunk
CHUNK_OVERLAP = 150    # overlap between consecutive chunks
MIN_CHUNK_CHARS = 80   # discard chunks shorter than this


def _extract_text_from_pdf(pdf_path: str) -> list[dict]:
    """
    Extract text page by page using PyMuPDF.
    Returns list of {page, text} dicts.
    Falls back to pytesseract OCR for pages with too little text.
    """
    pages = []
    doc = fitz.open(pdf_path)

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text").strip()

        if len(text) < 50:
            # Likely a scanned/image page — OCR it
            text = _ocr_page(page)

        pages.append({"page": page_num + 1, "text": text})

    doc.close()
    return pages


def _ocr_page(page) -> str:
    """Render page to image and run Tesseract OCR."""
    try:
        import pytesseract
        from PIL import Image
        import io

        mat = fitz.Matrix(2.0, 2.0)  # 2x scale for better OCR
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        text = pytesseract.image_to_string(img, config="--psm 6")
        return text.strip()
    except Exception as e:
        logger.warning(f"OCR failed for page: {e}")
        return ""


def _detect_section(text: str, page: int) -> Optional[str]:
    """Heuristic: detect section headings from text."""
    lines = text.split("\n")
    for line in lines[:5]:  # Check first 5 lines
        line = line.strip()
        # Match patterns like "3.2 Fault Codes" or "SECTION 4: MAINTENANCE"
        if re.match(r"^(\d+[\.\d]*\s+\w|[A-Z][A-Z\s]{4,}$)", line) and len(line) < 100:
            return line
    return None


def _chunk_page_text(page_num: int, text: str) -> list[dict]:
    """
    Split page text into overlapping chunks.
    Returns list of {page, section, text} dicts.
    """
    if not text or len(text) < MIN_CHUNK_CHARS:
        return []

    section = _detect_section(text, page_num)
    chunks = []
    start = 0

    while start < len(text):
        end = start + CHUNK_SIZE
        chunk_text = text[start:end].strip()

        if len(chunk_text) >= MIN_CHUNK_CHARS:
            chunks.append({
                "page": page_num,
                "section": section,
                "text": chunk_text,
            })

        if end >= len(text):
            break
        start = end - CHUNK_OVERLAP

    return chunks


def ingest_document(db: Session, document_id: str) -> None:
    """
    Full ingestion pipeline for a document.
    Updates document status in DB throughout.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        logger.error(f"Document not found: {document_id}")
        return

    doc.ingestion_status = IngestionStatus.processing
    db.commit()

    pdf_path = os.path.join(settings.upload_dir, doc.filename)

    try:
        # 1. Extract text
        logger.info(f"Extracting text from: {doc.filename}")
        pages = _extract_text_from_pdf(pdf_path)
        doc.page_count = len(pages)

        # 2. Chunk
        all_chunks = []
        for p in pages:
            all_chunks.extend(_chunk_page_text(p["page"], p["text"]))

        if not all_chunks:
            raise ValueError("No extractable text found in document")

        logger.info(f"Generated {len(all_chunks)} chunks from {len(pages)} pages")

        # 3. Embed (batch)
        embedding_svc = get_embedding_service()
        texts = [c["text"] for c in all_chunks]
        vectors = embedding_svc.embed(texts)

        # 4. Save chunks to DB + Qdrant
        vector_store = get_vector_store()
        qdrant_points = []
        db_chunks = []

        for i, chunk in enumerate(all_chunks):
            chunk_id = f"{document_id}_{i}"
            db_chunk = DocumentChunk(
                id=chunk_id,
                document_id=document_id,
                page=chunk["page"],
                section=chunk.get("section"),
                text=chunk["text"],
                char_count=len(chunk["text"]),
            )
            db_chunks.append(db_chunk)

            qdrant_points.append({
                "chunk_id": chunk_id,
                "vector": vectors[i],
                "document_id": document_id,
                "document_title": doc.title,
                "equipment_id": doc.equipment_id,
                "page": chunk["page"],
                "section": chunk.get("section"),
                "text": chunk["text"],
            })

        db.bulk_save_objects(db_chunks)
        point_ids = vector_store.upsert_chunks(qdrant_points)

        # Store qdrant IDs back to chunks
        for i, chunk in enumerate(db_chunks):
            if i < len(point_ids):
                chunk.qdrant_point_id = str(point_ids[i])

        doc.ingestion_status = IngestionStatus.complete
        db.commit()
        logger.info(f"Ingestion complete: {document_id} — {len(db_chunks)} chunks indexed")

    except Exception as e:
        logger.exception(f"Ingestion failed for {document_id}: {e}")
        doc.ingestion_status = IngestionStatus.failed
        doc.error_message = str(e)[:500]
        db.commit()

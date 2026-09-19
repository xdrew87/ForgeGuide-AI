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


def _bbox_overlap_ratio(block_bbox: tuple, table_bbox: tuple) -> float:
    """Fraction of block_bbox's area covered by table_bbox."""
    bx0, by0, bx1, by1 = block_bbox
    tx0, ty0, tx1, ty1 = table_bbox
    ix0, iy0 = max(bx0, tx0), max(by0, ty0)
    ix1, iy1 = min(bx1, tx1), min(by1, ty1)
    if ix1 <= ix0 or iy1 <= iy0:
        return 0.0
    inter = (ix1 - ix0) * (iy1 - iy0)
    block_area = max((bx1 - bx0) * (by1 - by0), 1e-6)
    return inter / block_area


def _extract_tables_from_page(page, page_num: int) -> list[dict]:
    """Detect tables via PyMuPDF's find_tables() (ruling-line/text-alignment based)."""
    tables = []
    try:
        found = page.find_tables()
    except Exception as e:
        logger.warning(f"Table detection failed on page {page_num}: {e}")
        return tables

    for tab in found.tables:
        rows = tab.extract()
        if not rows:
            continue
        tables.append({"page": page_num, "bbox": tuple(tab.bbox), "rows": rows})
    return tables


def _table_to_markdown(rows: list[list], max_chars: int = 4000) -> str:
    """Render extracted table rows as a markdown pipe table."""
    if not rows:
        return ""

    def cell(v):
        return "" if v is None else str(v).replace("\n", " ").strip()

    header = rows[0]
    lines = ["| " + " | ".join(cell(c) for c in header) + " |"]
    lines.append("| " + " | ".join("---" for _ in header) + " |")
    for row in rows[1:]:
        lines.append("| " + " | ".join(cell(c) for c in row) + " |")

    md = "\n".join(lines)
    if len(md) > max_chars:
        md = md[:max_chars] + "\n...(truncated)"
    return md


def _extract_text_from_pdf(pdf_path: str) -> list[dict]:
    """
    Extract text and tables page by page using PyMuPDF.
    Returns list of {page, text, tables} dicts.
    Falls back to pytesseract OCR for pages with too little text and no
    detected tables (a table-only page legitimately has little prose left
    once table content is excluded — that's expected, not a scan).
    """
    pages = []
    doc = fitz.open(pdf_path)

    for page_num in range(len(doc)):
        page = doc[page_num]
        tables = _extract_tables_from_page(page, page_num + 1)

        if tables:
            # Exclude prose blocks that overlap a detected table so the
            # table's raw cell text isn't also duplicated into a text chunk.
            table_bboxes = [t["bbox"] for t in tables]
            kept = []
            for b in page.get_text("blocks"):
                bx0, by0, bx1, by1, btext = b[0], b[1], b[2], b[3], b[4]
                block_type = b[6] if len(b) > 6 else 0
                if block_type != 0:
                    continue
                if any(_bbox_overlap_ratio((bx0, by0, bx1, by1), tb) > 0.6 for tb in table_bboxes):
                    continue
                if btext.strip():
                    kept.append(btext.strip())
            text = "\n".join(kept).strip()
        else:
            text = page.get_text("text").strip()

        if len(text) < 50 and not tables:
            # Likely a scanned/image page — OCR it
            text = _ocr_page(page)

        pages.append({"page": page_num + 1, "text": text, "tables": tables})

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

        # 2. Chunk (prose, page-scoped sliding window) + tables (whole chunk each)
        all_chunks = []
        for p in pages:
            text_chunks = _chunk_page_text(p["page"], p["text"])
            for c in text_chunks:
                c["chunk_type"] = "text"
            all_chunks.extend(text_chunks)

            for tbl in p.get("tables", []):
                markdown = _table_to_markdown(tbl["rows"])
                if not markdown.strip():
                    continue
                section = _detect_section(p["text"], p["page"]) or f"Table (page {p['page']})"
                all_chunks.append({
                    "page": tbl["page"],
                    "section": section,
                    "text": markdown,
                    "chunk_type": "table",
                })

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
            chunk_type = chunk.get("chunk_type", "text")
            db_chunk = DocumentChunk(
                id=chunk_id,
                document_id=document_id,
                page=chunk["page"],
                section=chunk.get("section"),
                text=chunk["text"],
                char_count=len(chunk["text"]),
                chunk_type=chunk_type,
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
                "chunk_type": chunk_type,
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

import os
import re
import uuid
import logging
import threading
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db, SessionLocal
from app.models.models import Document, DocumentChunk, IngestionStatus
from app.services.highlights import find_highlight_rects, find_table_highlight_rects, render_page_image

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_EXTENSIONS = set(settings.allowed_extensions.split(","))
MAX_BYTES = settings.max_upload_size_mb * 1024 * 1024


def _safe_filename(name: str) -> str:
    """Sanitize filename — keep only safe chars."""
    name = Path(name).name  # strip any path components
    name = re.sub(r"[^\w\.\-]", "_", name)
    return name[:200]


class DocumentOut(BaseModel):
    id: str
    title: str
    filename: str
    original_filename: str
    page_count: int | None
    ingestion_status: str
    equipment_id: str | None
    error_message: str | None

    model_config = {"from_attributes": True}


class ChunkOut(BaseModel):
    id: str
    page: int
    section: str | None
    text: str
    chunk_type: str

    model_config = {"from_attributes": True}


class RectOut(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float


class HighlightsOut(BaseModel):
    page_width: float
    page_height: float
    rects: list[RectOut]


@router.post("/upload", response_model=DocumentOut, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    equipment_id: str = Form(None),
    version: str = Form(None),
    db: Session = Depends(get_db),
):
    # Validate extension
    ext = Path(file.filename).suffix.lower().lstrip(".")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Only {ALLOWED_EXTENSIONS} files accepted")

    # Read and size-check
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_upload_size_mb}MB limit")

    # Save to uploads dir
    safe_orig = _safe_filename(file.filename)
    stored_name = f"{uuid.uuid4().hex}_{safe_orig}"
    upload_path = os.path.join(settings.upload_dir, stored_name)

    os.makedirs(settings.upload_dir, mode=0o700, exist_ok=True)
    with open(upload_path, "wb") as f:
        f.write(data)

    # Create DB record
    doc = Document(
        equipment_id=equipment_id or None,
        title=title.strip()[:500],
        version=(version or "").strip()[:60] or None,
        filename=stored_name,
        original_filename=safe_orig,
        ingestion_status=IngestionStatus.pending,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Kick off ingestion in background thread (keeps API responsive)
    def _ingest(doc_id: str):
        from app.services.ingestion import ingest_document
        from app.db.session import get_db as _get_db_gen
        sess_gen = _get_db_gen()
        sess = next(sess_gen)
        try:
            ingest_document(sess, doc_id)
        finally:
            try:
                next(sess_gen)
            except StopIteration:
                pass

    t = threading.Thread(target=_ingest, args=(doc.id,), daemon=True)
    t.start()

    logger.info(f"Uploaded document {doc.id} ({safe_orig}), ingestion started")
    return doc


@router.get("/", response_model=list[DocumentOut])
def list_documents(equipment_id: str = None, db: Session = Depends(get_db)):
    q = db.query(Document)
    if equipment_id:
        q = q.filter(Document.equipment_id == equipment_id)
    return q.order_by(Document.created_at.desc()).all()


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.get("/{document_id}/chunks", response_model=list[ChunkOut])
def get_chunks(document_id: str, page: int = None, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    q = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id)
    if page is not None:
        q = q.filter(DocumentChunk.page == page)
    return q.order_by(DocumentChunk.page).all()


@router.get("/{document_id}/pages/{page_number}/image")
def get_page_image(document_id: str, page_number: int, scale: float = 2.0, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.page_count and page_number > doc.page_count:
        raise HTTPException(status_code=404, detail="Page out of range")

    pdf_path = os.path.join(settings.upload_dir, doc.filename)
    scale = max(0.5, min(scale, 4.0))
    png_bytes = render_page_image(pdf_path, page_number, scale=scale)
    if png_bytes is None:
        raise HTTPException(status_code=404, detail="Page out of range")

    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@router.get("/{document_id}/pages/{page_number}/highlights", response_model=HighlightsOut)
def get_page_highlights(
    document_id: str,
    page_number: int,
    chunk_id: str = None,
    excerpt: str = None,
    db: Session = Depends(get_db),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    search_text = None
    chunk = None
    if chunk_id:
        chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        if chunk:
            search_text = chunk.text
    if not search_text:
        search_text = excerpt or ""

    if not search_text.strip():
        raise HTTPException(status_code=400, detail="chunk_id or excerpt is required")

    pdf_path = os.path.join(settings.upload_dir, doc.filename)
    if chunk is not None and chunk.chunk_type == "table":
        # For a table the excerpt param carries the LLM's quoted cell text.
        page_width, page_height, rects = find_table_highlight_rects(
            pdf_path, page_number, chunk.text, excerpt or ""
        )
    else:
        page_width, page_height, rects = find_highlight_rects(pdf_path, page_number, search_text)
    return HighlightsOut(
        page_width=page_width,
        page_height=page_height,
        rects=[RectOut(x0=r[0], y0=r[1], x1=r[2], y1=r[3]) for r in rects],
    )


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Remove from Qdrant
    try:
        from app.services.vector_store import get_vector_store
        get_vector_store().delete_by_document(document_id)
    except Exception as e:
        logger.warning(f"Vector deletion failed: {e}")

    # Remove file
    file_path = os.path.join(settings.upload_dir, doc.filename)
    try:
        os.remove(file_path)
    except FileNotFoundError:
        pass

    db.delete(doc)
    db.commit()

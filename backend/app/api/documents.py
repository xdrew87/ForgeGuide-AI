import os
import re
import uuid
import logging
import threading
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db, SessionLocal
from app.models.models import Document, DocumentChunk, IngestionStatus

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

    model_config = {"from_attributes": True}


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

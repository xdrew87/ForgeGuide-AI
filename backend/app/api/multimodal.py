import os
import uuid
import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.vision import extract_fault_codes
from app.services.qa import answer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/multimodal", tags=["multimodal"])

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10MB


class FaultAnalysisResponse(BaseModel):
    raw_text: str
    fault_codes: list[str]
    suggested_query: str
    qa_answer: str | None
    qa_citations: list[dict]
    qa_evidence_sufficient: bool
    qa_confidence: float


@router.post("/analyze-image", response_model=FaultAnalysisResponse)
async def analyze_image(
    file: UploadFile = File(...),
    equipment_id: str = Form(None),
    db: Session = Depends(get_db),
):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Supported image types: {ALLOWED_IMAGE_EXTENSIONS}")

    data = await file.read()
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image too large (max 10MB)")

    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name

    try:
        extraction = extract_fault_codes(tmp_path)
        suggested_query = extraction["suggested_query"]

        # If we got something, run QA
        qa_answer = None
        qa_citations = []
        qa_sufficient = False
        qa_confidence = 0.0

        if suggested_query:
            result = answer(db, suggested_query, equipment_id=equipment_id)
            qa_answer = result.answer
            qa_citations = [
                {
                    "document": c.document,
                    "page": c.page,
                    "section": c.section,
                    "excerpt": c.excerpt,
                    "chunk_id": c.chunk_id,
                    "document_id": c.document_id,
                }
                for c in result.citations
            ]
            qa_sufficient = result.evidence_sufficient
            qa_confidence = result.confidence

        return FaultAnalysisResponse(
            raw_text=extraction["raw_text"],
            fault_codes=extraction["fault_codes"],
            suggested_query=suggested_query,
            qa_answer=qa_answer,
            qa_citations=qa_citations,
            qa_evidence_sufficient=qa_sufficient,
            qa_confidence=qa_confidence,
        )

    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

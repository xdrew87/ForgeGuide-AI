import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import Conversation, Message, MessageRole
from app.services.qa import answer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


class AskRequest(BaseModel):
    question: str
    equipment_id: str | None = None
    conversation_id: str | None = None


class CitationOut(BaseModel):
    document: str
    page: int
    section: str | None
    excerpt: str
    chunk_id: str
    document_id: str


class AskResponse(BaseModel):
    conversation_id: str
    message_id: str
    question: str
    answer: str
    citations: list[CitationOut]
    evidence_sufficient: bool
    confidence: float
    chunks_used: int


@router.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest, db: Session = Depends(get_db)):
    q = payload.question.strip()
    if not q:
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    if len(q) > 2000:
        raise HTTPException(status_code=400, detail="Question too long (max 2000 chars)")

    # Get or create conversation
    conv = None
    if payload.conversation_id:
        conv = db.query(Conversation).filter(Conversation.id == payload.conversation_id).first()

    if not conv:
        conv = Conversation(equipment_id=payload.equipment_id)
        db.add(conv)
        db.commit()
        db.refresh(conv)

    # Save user message
    user_msg = Message(
        conversation_id=conv.id,
        role=MessageRole.user,
        content=q,
    )
    db.add(user_msg)
    db.commit()

    # Run QA
    try:
        result = answer(db, q, equipment_id=payload.equipment_id or conv.equipment_id)
    except Exception as e:
        logger.exception(f"QA error: {e}")
        raise HTTPException(status_code=500, detail="QA pipeline error")

    # Save assistant message
    asst_msg = Message(
        conversation_id=conv.id,
        role=MessageRole.assistant,
        content=result.answer,
        citations_json=json.dumps([
            {
                "document": c.document,
                "page": c.page,
                "section": c.section,
                "excerpt": c.excerpt,
                "chunk_id": c.chunk_id,
                "document_id": c.document_id,
            }
            for c in result.citations
        ]),
        confidence=result.confidence,
        evidence_sufficient=result.evidence_sufficient,
    )
    db.add(asst_msg)
    db.commit()
    db.refresh(asst_msg)

    return AskResponse(
        conversation_id=conv.id,
        message_id=asst_msg.id,
        question=q,
        answer=result.answer,
        citations=[
            CitationOut(
                document=c.document,
                page=c.page,
                section=c.section,
                excerpt=c.excerpt,
                chunk_id=c.chunk_id,
                document_id=c.document_id,
            )
            for c in result.citations
        ],
        evidence_sufficient=result.evidence_sufficient,
        confidence=result.confidence,
        chunks_used=result.chunks_used,
    )


@router.get("/conversations/{conversation_id}/messages")
def get_messages(conversation_id: str, db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at).all()

    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "citations": json.loads(m.citations_json) if m.citations_json else [],
            "confidence": m.confidence,
            "evidence_sufficient": m.evidence_sufficient,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]

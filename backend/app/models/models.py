import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime,
    ForeignKey, Enum as SAEnum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base
import enum

Base = declarative_base()


def new_uuid():
    return str(uuid.uuid4())


class IngestionStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    complete = "complete"
    failed = "failed"


class MessageRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(String, primary_key=True, default=new_uuid)
    manufacturer = Column(String(255), nullable=False)
    model = Column(String(255), nullable=False)
    equipment_type = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    documents = relationship("Document", back_populates="equipment")
    conversations = relationship("Conversation", back_populates="equipment")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=new_uuid)
    equipment_id = Column(String, ForeignKey("equipment.id"), nullable=True)
    title = Column(String(512), nullable=False)
    version = Column(String(64), nullable=True)
    filename = Column(String(512), nullable=False)
    original_filename = Column(String(512), nullable=False)
    page_count = Column(Integer, nullable=True)
    ingestion_status = Column(
        SAEnum(IngestionStatus),
        default=IngestionStatus.pending,
        nullable=False
    )
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    equipment = relationship("Equipment", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String, primary_key=True, default=new_uuid)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    page = Column(Integer, nullable=False)
    section = Column(String(512), nullable=True)
    text = Column(Text, nullable=False)
    char_count = Column(Integer, nullable=False)
    qdrant_point_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="chunks")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=new_uuid)
    equipment_id = Column(String, ForeignKey("equipment.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    equipment = relationship("Equipment", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=new_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(SAEnum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    # Answer metadata stored as JSON string
    citations_json = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    evidence_sufficient = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")

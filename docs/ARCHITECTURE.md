# ForgeGuide AI — Architecture

## System Overview

ForgeGuide AI is a RAG (Retrieval-Augmented Generation) application purpose-built for industrial maintenance. Its distinguishing constraint: the LLM layer is gated — it cannot produce a response unless the retrieval layer first surfaces documentary evidence above a confidence threshold.

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                            │
│   Next.js · Tailwind · TypeScript                           │
│                                                             │
│   DocumentUploader → EquipmentManager → ChatInterface       │
│                              ↕                              │
│                        CitationPanel                        │
└───────────────────────────┬─────────────────────────────────┘
                            │ REST/JSON
┌───────────────────────────▼─────────────────────────────────┐
│                    FastAPI Backend                           │
│                                                             │
│  /api/v1/equipment/     Equipment CRUD                      │
│  /api/v1/documents/     Upload · Status · Chunks            │
│  /api/v1/chat/ask       Grounded QA                         │
│  /api/v1/multimodal/    Image analysis + fault retrieval    │
└──────────┬──────────────────────────────────────────────────┘
           │
    ┌──────▼──────────────────────────────────────────┐
    │              Service Layer                       │
    │                                                 │
    │  ingestion.py   PDF → text → chunks → embed     │
    │  retrieval.py   Qdrant semantic + SQL keyword    │
    │                 → RRF fusion                    │
    │  qa.py          Evidence gate → LLM → citations │
    │  vision.py      Image OCR / LLM vision          │
    │  embedding.py   Provider-agnostic embeddings    │
    │  vector_store.py Qdrant client wrapper          │
    └──────┬────────────────────┬────────────────────┘
           │                    │
    ┌──────▼──────┐      ┌──────▼──────┐
    │ PostgreSQL  │      │   Qdrant    │
    │             │      │             │
    │ equipment   │      │ chunk       │
    │ documents   │      │ vectors     │
    │ doc_chunks  │      │ + payload   │
    │ conversations│     │             │
    │ messages    │      └─────────────┘
    └─────────────┘
```

## Document Ingestion Pipeline

```
PDF upload
    │
    ▼
File validation (extension, size, filename sanitization)
    │
    ▼
Stored to /uploads with UUID prefix
    │
    ▼
PyMuPDF text extraction (page by page)
    │
    ├─ Text found? → proceed
    └─ Sparse/empty page → Tesseract OCR (2× scale render)
    │
    ▼
Chunking: 800-char windows, 150-char overlap, page number preserved
    │
    ▼
Section heuristic: detect headings in first 5 lines of each page
    │
    ▼
Batch embedding (Anthropic Voyage or OpenAI)
    │
    ├─ Qdrant: upsert vectors with payload (chunk_id, doc_id, equipment_id, page, section, text)
    └─ PostgreSQL: insert DocumentChunk rows with qdrant_point_id
    │
    ▼
Document status: complete / failed
```

## Hybrid Retrieval (RRF)

Two signals fused via Reciprocal Rank Fusion:

1. **Semantic** (Qdrant): cosine similarity on query embedding, optional equipment_id filter, score threshold 0.2
2. **Keyword** (SQL ILIKE): OR-of-keywords against chunk text, same equipment filter

RRF formula: `score(chunk) = Σ 1 / (k + rank_i)` where k=60

Chunks appearing in both lists receive higher fused scores. Top 6 returned.

## Evidence Gate (QA)

```python
confidence = avg_retrieval_score × coverage_factor

if not chunks or confidence < THRESHOLD (0.45):
    return <<INSUFFICIENT_EVIDENCE>> response
else:
    call LLM with context + strict grounding prompt
```

The LLM system prompt prohibits:
- Inventing procedures
- Bypassing safety controls
- Responding without context evidence

## Multimodal Flow

```
Image upload
    │
    ▼
LLM vision (Claude/GPT-4o) OR Tesseract OCR
    │
    ▼
Fault code regex extraction (e.g. E17, F03, A-400)
    │
    ▼
Suggested query built from detected codes
    │
    ▼
Full retrieval + QA pipeline (same as text)
    │
    ▼
Return: raw_text, fault_codes, suggested_query, qa_answer, citations
```

## Data Model

```
Equipment (id, manufacturer, model, equipment_type)
    │ 1:N
Document (id, equipment_id, title, version, filename, ingestion_status, page_count)
    │ 1:N
DocumentChunk (id, document_id, page, section, text, char_count, qdrant_point_id)

Conversation (id, equipment_id)
    │ 1:N
Message (id, conversation_id, role, content, citations_json, confidence, evidence_sufficient)
```

## LLM Provider Abstraction

The system is not coupled to any single LLM vendor. `LLM_PROVIDER` and `LLM_MODEL` env vars control routing. Currently supported: `anthropic` (Claude), `openai` (GPT-4 family). The embedding layer is similarly abstracted.

## Deployment

Docker Compose with four services:
- `db` (Postgres 16)
- `qdrant` (Qdrant 1.9)
- `backend` (FastAPI + uvicorn)
- `frontend` (Next.js)

No Kubernetes. Compatible with future private/on-prem deployment by pointing env vars at local model endpoints.

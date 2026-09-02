# Hackathon Submission — ForgeGuide AI

**Event:** ABB Accelerator 2026
**Theme:** Theme 2 — Multimodal Maintenance Intelligence Agent
**Project:** ForgeGuide AI

---

## Project Summary

ForgeGuide AI is an evidence-grounded multimodal industrial maintenance assistant. Technicians ask maintenance questions and receive answers traced to specific pages and sections of uploaded technical documentation. If documentation evidence is insufficient, the system explicitly declines rather than fabricating a procedure.

**Core principle:** No evidence = no maintenance recommendation.

---

## Problem Statement

Industrial technicians often troubleshoot complex equipment under time pressure without reliable access to the relevant section of a manual. Existing LLM-based assistants generate plausible-sounding but potentially fabricated procedures — a safety risk in industrial settings.

---

## Solution

A RAG (Retrieval-Augmented Generation) system with a hard evidence gate:

1. Upload technical manuals (PDF, scanned)
2. System indexes content by page, section, and equipment model
3. Technician asks a question in natural language
4. System retrieves matching documentation (hybrid semantic + keyword search)
5. If evidence meets confidence threshold → LLM generates grounded answer with citations
6. If evidence is insufficient → system explicitly declines
7. Optionally: upload equipment panel photo → fault codes extracted → documentation retrieved automatically

---

## Key Differentiators

- **Evidence gate**: retrieval confidence threshold enforced before LLM call
- **Citation-first UX**: every factual claim maps to a document, page, and section
- **Safety constraints**: system prompt prohibits bypassing LOTO, interlocks, or safety systems
- **Multimodal**: camera → fault code → documentation → procedure
- **Provider-agnostic**: Anthropic or OpenAI via env var swap
- **On-prem ready**: Docker Compose, no mandatory cloud dependencies

---

## Technical Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, Tailwind CSS, TypeScript |
| Backend | Python, FastAPI |
| Database | PostgreSQL 16 |
| Vector DB | Qdrant 1.19 |
| PDF extraction | PyMuPDF |
| OCR | Tesseract |
| LLM | Anthropic Claude (or OpenAI) |
| Embeddings | Anthropic Voyage (or OpenAI) |
| Deployment | Docker Compose |

---

## Demo Deliverables

- **Working prototype**: `docker-compose up --build` → running application
- **Demo manual**: synthetic MX-400 maintenance PDF (19KB, 8 pages, realistic content)
- **Primary demo scenario**: E17 thermal fault diagnosis with full citation chain
- **No-evidence scenario**: query with no supporting docs → explicit refusal (no fabrication)
- **Multimodal scenario**: equipment image → fault code extraction → documentation retrieval

---

## Source Code

Repository structure is self-contained and documented. See README.md for setup instructions.

---

## Test Coverage

23 automated tests including a named regression:

> `TestNoEvidenceBehavior::test_answer_contains_no_fabrication_marker`
> When no supporting documentation exists, ForgeGuide does not generate a maintenance procedure.

---

## Limitations / Future Work

- No authentication (would add for production)
- Single-user (no multi-tenancy)
- Evidence confidence is a heuristic, not a calibrated probability
- No streaming responses (single-turn per request)
- Predictive maintenance ML out of scope

# ForgeGuide AI

**Evidence-grounded multimodal industrial maintenance assistant**
ABB Accelerator 2026 — Theme 2: Multimodal Maintenance Intelligence Agent

> **Core principle:** No evidence = no maintenance recommendation. ForgeGuide AI never fabricates procedures.

---

## Demo Flow

1. Upload a technical manual (PDF)
2. System processes, extracts, and indexes it
3. Select an equipment model
4. Ask a maintenance question
5. Retrieve relevant documentation
6. Receive a grounded, citation-backed answer
7. Click any citation to view the supporting source text
8. Optionally upload an equipment image — fault codes are detected and matched to documentation

**Example query:**
> "The MX-400 keeps showing E17 after running under load for 20 minutes. What should I check?"

**Expected result:**
- Identifies E17 from uploaded documentation
- Lists troubleshooting steps supported by the manual
- Cites exact manual pages and sections
- Shows evidence confidence indicator
- Declines to answer if supporting evidence is insufficient

---

## Quick Start

### Prerequisites

- Docker Desktop
- Python 3.11+
- An Anthropic or OpenAI API key

> **Intel MacBook Pro:** Use Anthropic or OpenAI. Ollama inside Docker on Intel Mac has no GPU access — responses take 60–300 seconds and are not usable for a demo. Ollama works on Apple Silicon (M1/M2/M3/M4), Linux+NVIDIA, or Windows+NVIDIA.

### 1. Clone and configure

```bash
git clone <repo>
cd forgeguide
cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY (or OPENAI_API_KEY + LLM_PROVIDER=openai)
```

### 2. Start all services

```bash
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs
- Qdrant dashboard: http://localhost:6333/dashboard

### 3. Load demo data

```bash
# Generate the synthetic MX-400 demo manual
python scripts/generate_demo_manual.py

# Then upload it via the UI or API:
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@demo-data/MX400-Maintenance-Manual-DEMO.pdf" \
  -F "title=MX-400 Maintenance Manual (DEMO)"
```

### 4. Create demo equipment (optional, for filtering)

```bash
curl -X POST http://localhost:8000/api/v1/equipment/ \
  -H "Content-Type: application/json" \
  -d '{"manufacturer":"Demo","model":"MX-400","equipment_type":"Motor Drive"}'
```

---

## Architecture

```
frontend (Next.js)
    │  REST JSON
    ▼
backend (FastAPI / Python)
    ├── Document ingestion (PyMuPDF + Tesseract OCR)
    ├── Hybrid retrieval (Qdrant semantic + SQL keyword → RRF)
    ├── Grounded QA (LLM with evidence gate)
    └── Vision / fault code extraction
    │
    ├── PostgreSQL  (documents, chunks, conversations, messages)
    └── Qdrant      (vector embeddings)
```

Full details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

23 tests covering: PDF extraction, chunking, upload validation, no-evidence regression, citation parsing, fault code extraction, RRF fusion.

---

## Project Structure

```
forgeguide/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routers
│   │   ├── core/         # Config, settings
│   │   ├── db/           # Database session
│   │   ├── models/       # SQLAlchemy models
│   │   └── services/     # ingestion, retrieval, qa, vision, embedding, vector_store
│   └── tests/
├── frontend/
│   └── src/
│       ├── components/   # ChatInterface, CitationPanel, DocumentUploader, EquipmentManager
│       ├── lib/          # API client
│       └── pages/        # Next.js pages
├── demo-data/            # Synthetic MX-400 manual PDF
├── docs/                 # Architecture, security, demo, hackathon docs
├── scripts/              # generate_demo_manual.py
├── docker-compose.yml
└── .env.example
```

---

## Safety Constraints

- No maintenance procedures generated without documentary evidence
- Safety-critical content explicitly flagged `[SAFETY-CRITICAL]`
- Never recommends disabling lockout/tagout, interlocks, or safety controls
- All content clearly marked EVIDENCE vs SYNTHESIS

See [docs/SECURITY.md](docs/SECURITY.md) for full security model.

---

## Demo Content

The synthetic `MX400-Maintenance-Manual-DEMO.pdf` is entirely fictional content created for demonstration. It does not represent any real ABB or third-party product.

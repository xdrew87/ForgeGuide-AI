# ForgeGuide AI

**Evidence-grounded multimodal industrial maintenance assistant**

[![CI](https://github.com/xdrew87/ForgeGuide-AI/actions/workflows/ci.yml/badge.svg)](https://github.com/xdrew87/ForgeGuide-AI/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](backend)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black.svg)](frontend)
[![Docker Compose](https://img.shields.io/badge/Deploy-Docker%20Compose-2496ED.svg)](docker-compose.yml)

Built for **ABB Accelerator 2026 — Theme 2: Multimodal Maintenance Intelligence Agent.**

> ### Core principle: no evidence, no answer.
> ForgeGuide AI is a retrieval-augmented assistant with a hard evidence gate
> in front of the LLM. If the retrieved documentation doesn't clear a
> confidence threshold, the system declines to answer instead of guessing —
> it never fabricates a maintenance procedure.

---

## Contents

- [How it works](#how-it-works)
- [Stack](#stack)
- [Quick start](#quick-start)
- [Common commands](#common-commands)
- [Architecture](#architecture)
- [Running tests](#running-tests)
- [Project structure](#project-structure)
- [Safety constraints](#safety-constraints)
- [Demo content](#demo-content)
- [Contributing](#contributing)
- [License](#license)

---

## How it works

1. Upload a technical manual (PDF, including scanned pages via OCR fallback)
2. The document is chunked, embedded, and indexed by page and section
3. A technician asks a maintenance question in plain language
4. Hybrid retrieval (semantic + keyword search, fused with RRF) pulls the
   relevant passages
5. **If retrieval confidence clears the threshold** → the LLM answers
   strictly from the retrieved context and cites page/section for every claim
6. **If it doesn't** → the system returns an explicit `INSUFFICIENT_EVIDENCE`
   response — no answer is better than a wrong one
7. Optionally, upload a photo of an equipment fault display — fault codes are
   extracted (vision model or OCR) and matched against the indexed manuals

**Try it** (against the included synthetic demo manual):

> "The MX-400 shows E17 after 20 minutes under load. What should I check?"

Expected: a grounded answer citing the manual's fault-code table and Section
6.3 thermal fault procedure, with a confidence score. Asking something the
manual doesn't cover (e.g. "how do I reprogram the PLC?") should instead
return the insufficient-evidence refusal.

---

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 15, React 18, Tailwind CSS, TypeScript |
| Backend | Python 3.12, FastAPI, SQLAlchemy |
| Database | PostgreSQL 16 |
| Vector DB | Qdrant |
| PDF / OCR | PyMuPDF, Tesseract |
| LLM & embeddings | Anthropic, OpenAI, or local Ollama (pick any one) |
| Deployment | Docker Compose |

---

## Quick start

### Prerequisites

- Docker Desktop
- Python 3.11+
- One of: an Anthropic API key, an OpenAI API key, or [Ollama](https://ollama.com) running locally via Docker
- Windows only: [PowerShell 7+](https://learn.microsoft.com/powershell/scripting/install/installing-powershell) (`pwsh`) — `setup.ps1` and `make.ps1` don't run on the older Windows PowerShell 5.1

> **Apple Silicon / Linux+NVIDIA / Windows+NVIDIA** — Ollama runs well locally, no API key needed.
> **Intel Mac** — Ollama has no GPU access in Docker, so local inference can take 60–300 seconds per response. It still works, but Anthropic or OpenAI feel much more responsive for a live demo.

### 1. Clone and configure

**macOS / Linux:**

```bash
git clone https://github.com/xdrew87/ForgeGuide-AI.git
cd ForgeGuide-AI
bash setup.sh
```

**Windows (PowerShell 7+):**

```powershell
git clone https://github.com/xdrew87/ForgeGuide-AI.git
cd ForgeGuide-AI
.\setup.ps1
```

Both scripts do the same thing: create `.env` from the template if it
doesn't exist (macOS additionally detects Intel hardware and warns about
Ollama performance), generate the demo PDF, and build/start every service.
Edit `.env` first (or answer the prompts) to pick a provider:

```bash
LLM_PROVIDER=anthropic          # anthropic | openai | ollama
LLM_MODEL=claude-sonnet-4-6
ANTHROPIC_API_KEY=...

EMBEDDING_PROVIDER=anthropic
EMBEDDING_MODEL=voyage-3-lite
EMBEDDING_DIM=1024
```

If you're using Ollama, pull the models it needs after the stack is up:

```bash
make ollama-pull-llm      # llama3.2 by default
make ollama-pull-embed    # nomic-embed-text by default
```

Windows without `make` on PATH:

```powershell
.\make.ps1 ollama-pull-llm
.\make.ps1 ollama-pull-embed
```

### 2. Open it

| Service | URL |
|---|---|
| App | http://localhost:3000 |
| API docs (Swagger) | http://localhost:8000/docs |
| Qdrant dashboard | http://localhost:6333/dashboard |

### 3. Load the demo manual

```bash
make seed
```

This creates a demo "MX-400" equipment record and uploads the included
synthetic `demo-data/MX400-Maintenance-Manual-DEMO.pdf`. Or do it by hand
through the UI's document uploader.

---

## Common commands

macOS / Linux (requires GNU Make):

```bash
make up             # start all services
make down            # stop all services
make rebuild         # rebuild images and restart (after code changes)
make logs            # tail all service logs
make logs-backend    # tail backend logs only
make test            # run the backend test suite
make seed            # create demo equipment + upload the demo manual
make clean           # stop and wipe all volumes (full reset)
make urls            # print service URLs
```

Windows (PowerShell 7+, no GNU Make required) — same targets via `make.ps1`:

```powershell
.\make.ps1 up
.\make.ps1 down
.\make.ps1 rebuild
.\make.ps1 logs
.\make.ps1 logs-backend
.\make.ps1 test
.\make.ps1 seed
.\make.ps1 clean
.\make.ps1 urls
```

**Ollama-specific:**

```bash
make ollama-list                       # see downloaded models
make ollama-pull-llm MODEL=mistral     # pull a different LLM
make ollama-pull-vision                # pull a vision model (llava) for image fault-code extraction
make ollama-run                        # interactive shell against the configured model
```

```powershell
.\make.ps1 ollama-list
.\make.ps1 ollama-pull-llm -Model mistral
.\make.ps1 ollama-pull-vision
.\make.ps1 ollama-run
```

---

## Architecture

```mermaid
flowchart TD
    FE["Frontend (Next.js)"] -->|"REST JSON, proxied through /api/v1"| BE["Backend (FastAPI)"]

    subgraph BE_INNER [" "]
        direction TB
        ING["Document ingestion<br/>PyMuPDF text extraction + Tesseract OCR fallback → chunking → embedding"]
        RET["Hybrid retrieval<br/>Qdrant semantic search + SQL keyword search, fused with RRF"]
        QA["Grounded QA<br/>evidence-gated LLM call, citations parsed from output"]
        VIS["Vision<br/>fault-code extraction from equipment photos"]
    end

    BE --> BE_INNER
    BE_INNER --> PG[("PostgreSQL<br/>documents, chunks, equipment, conversations, messages")]
    BE_INNER --> QD[("Qdrant<br/>chunk embeddings")]
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full design,
[docs/SECURITY.md](docs/SECURITY.md) for the safety/security model, and
[docs/DEMO.md](docs/DEMO.md) for a walkthrough script.

---

## Running tests

Against the running backend container:

```bash
docker compose exec backend python -m pytest tests/ -v
```

Or locally, without Docker (tests mock the DB and vector store, so no live
services are required):

```bash
cd backend
export DATABASE_URL=postgresql://test:test@localhost/test
export ANTHROPIC_API_KEY=test
python -m pytest tests/ -v
```

Windows (PowerShell):

```powershell
cd backend
$env:DATABASE_URL = "postgresql://test:test@localhost/test"
$env:ANTHROPIC_API_KEY = "test"
python -m pytest tests/ -v
```

23 tests covering PDF extraction, chunking, upload validation, the
no-fabrication evidence-gate regression, citation parsing, fault-code
extraction, and RRF fusion.

---

## Project structure

<details>
<summary>Click to expand</summary>

```
ForgeGuide-AI/
├── backend/
│   ├── app/
│   │   ├── api/          equipment, documents, chat, multimodal routers
│   │   ├── core/         config (pydantic-settings)
│   │   ├── db/           database session
│   │   ├── models/       SQLAlchemy models
│   │   └── services/     ingestion, retrieval, qa, vision, embedding, vector_store
│   └── tests/
├── frontend/
│   └── src/
│       ├── components/   ChatInterface, CitationPanel, DocumentUploader, EquipmentManager
│       ├── lib/          typed API client
│       └── pages/        Next.js pages + API proxy
├── demo-data/            synthetic MX-400 manual PDF
├── docs/                 architecture, security, demo script, hackathon writeup
├── scripts/              generate_demo_manual.py
├── docker-compose.yml
├── setup.sh              macOS / Linux setup
├── setup.ps1             Windows setup
├── Makefile              macOS / Linux task runner
└── make.ps1              Windows task runner
```

</details>

---

## Safety constraints

- No maintenance procedure is generated without supporting documentation
- Safety-critical content is explicitly flagged `[SAFETY-CRITICAL]`
- The system will never recommend disabling lockout/tagout, interlocks, or
  other protective controls
- Every answer distinguishes retrieved **evidence** from the model's
  **synthesis**, and cites the source document, page, and section

Full model: [docs/SECURITY.md](docs/SECURITY.md).

---

## Demo content

`demo-data/MX400-Maintenance-Manual-DEMO.pdf` is entirely synthetic — it does
not describe any real ABB or third-party product. Regenerate it with:

```bash
python3 scripts/generate_demo_manual.py   # or: make demo
```

```powershell
python scripts/generate_demo_manual.py    # or: .\make.ps1 demo
```

---

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) for setup,
the PR checklist, and the one rule that can't be bent: nothing gets merged
that weakens the evidence gate. Found a security issue? See
[SECURITY.md](SECURITY.md) instead of opening a public issue.

---

## License

MIT — see [LICENSE](LICENSE). Third-party dependency licenses are listed in
[docs/OPEN_SOURCE_LICENSES.md](docs/OPEN_SOURCE_LICENSES.md).

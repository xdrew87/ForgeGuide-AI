#!/usr/bin/env bash
set -e

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

info()    { echo -e "${GREEN}▶ $1${NC}"; }
warn()    { echo -e "${YELLOW}⚠  $1${NC}"; }
error()   { echo -e "${RED}✗ $1${NC}"; exit 1; }
section() { echo -e "\n${CYAN}${BOLD}$1${NC}"; echo "─────────────────────────────────────"; }

section "ForgeGuide AI — Setup"

# ── 1. Prerequisites ─────────────────────────────────────────────────────────
info "Checking prerequisites..."

command -v docker  >/dev/null 2>&1 || error "Docker not found. Install Docker Desktop: https://docker.com"
command -v python3 >/dev/null 2>&1 || error "Python 3 not found. Install: https://python.org"

PYTHON_VER=$(python3 -c 'import sys; print(sys.version_info[:2] >= (3,11))')
[ "$PYTHON_VER" = "True" ] || error "Python 3.11+ required (found $(python3 --version))"

docker info >/dev/null 2>&1 || error "Docker is not running. Start Docker Desktop first."

# Detect Intel vs Apple Silicon Mac
ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then
  IS_INTEL_MAC=true
else
  IS_INTEL_MAC=false
fi

echo "  Python: $(python3 --version)"
echo "  Docker: $(docker --version | head -1)"
echo "  CPU:    $(uname -m)"

# ── 2. Environment file ──────────────────────────────────────────────────────
section "Environment"

if [ ! -f .env ]; then
  cp .env.example .env

  if [ "$IS_INTEL_MAC" = "true" ]; then
    echo ""
    warn "Intel Mac detected."
    warn "Ollama is NOT recommended on Intel Mac — Docker has no GPU access"
    warn "and inference will be 60–300 seconds per response."
    echo ""
    echo "  Use Option A (Anthropic) or Option B (OpenAI) in .env."
    echo "  Both work great on Intel Mac."
    echo ""
  fi

  echo "  Open .env and set your API key, then press Enter."
  echo ""
  echo "  ${BOLD}Option A — Anthropic (recommended):${NC}"
  echo "    ANTHROPIC_API_KEY=sk-ant-..."
  echo ""
  echo "  ${BOLD}Option B — OpenAI:${NC}"
  echo "    LLM_PROVIDER=openai"
  echo "    OPENAI_API_KEY=sk-..."
  echo ""
  read -p "  Press Enter after editing .env to continue... "
else
  info ".env already exists"
fi

# Read provider
LLM_PROVIDER=$(grep -E "^LLM_PROVIDER=" .env | cut -d= -f2 | tr -d ' ')
echo "  Provider: ${LLM_PROVIDER:-not set}"

# Warn if someone tries Ollama on Intel Mac
if [ "$LLM_PROVIDER" = "ollama" ] && [ "$IS_INTEL_MAC" = "true" ]; then
  warn "You have LLM_PROVIDER=ollama set on an Intel Mac."
  warn "Ollama inside Docker on Intel has no GPU — expect 60–300s per response."
  echo ""
  read -p "  Continue anyway? (y/N): " CONFIRM
  [ "$CONFIRM" = "y" ] || [ "$CONFIRM" = "Y" ] || error "Change LLM_PROVIDER to anthropic or openai in .env and rerun."
fi

# ── 3. Demo manual ───────────────────────────────────────────────────────────
section "Demo data"

if [ ! -f demo-data/MX400-Maintenance-Manual-DEMO.pdf ]; then
  info "Generating synthetic MX-400 demo manual..."
  pip3 install reportlab --quiet 2>/dev/null || true
  python3 scripts/generate_demo_manual.py
else
  info "Demo PDF already exists"
fi

# ── 4. Docker services ───────────────────────────────────────────────────────
section "Docker services"
info "Building and starting services (first run: 3–5 min)..."
docker compose up -d --build

# ── 5. Pull Ollama models (only if provider=ollama and user confirmed above) ─
if [ "${LLM_PROVIDER}" = "ollama" ]; then
  section "Ollama models"

  LLM_MODEL=$(grep -E "^LLM_MODEL=" .env | cut -d= -f2 | tr -d ' ')
  LLM_MODEL=${LLM_MODEL:-llama3.2}
  EMBED_MODEL=$(grep -E "^EMBEDDING_MODEL=" .env | cut -d= -f2 | tr -d ' ')
  EMBED_MODEL=${EMBED_MODEL:-nomic-embed-text}
  VISION_MODEL=$(grep -E "^OLLAMA_VISION_MODEL=" .env | cut -d= -f2 | tr -d ' ')

  echo "  Waiting for Ollama container..."
  until curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; do
    printf "."; sleep 2
  done
  echo ""

  info "Pulling LLM: ${LLM_MODEL}"
  docker compose exec ollama ollama pull "${LLM_MODEL}"

  EMBED_PROVIDER=$(grep -E "^EMBEDDING_PROVIDER=" .env | cut -d= -f2 | tr -d ' ')
  if [ "${EMBED_PROVIDER}" = "ollama" ]; then
    info "Pulling embed model: ${EMBED_MODEL}"
    docker compose exec ollama ollama pull "${EMBED_MODEL}"
  fi

  if [ -n "${VISION_MODEL}" ]; then
    info "Pulling vision model: ${VISION_MODEL}"
    docker compose exec ollama ollama pull "${VISION_MODEL}"
  fi

  if [ "$IS_INTEL_MAC" = "true" ]; then
    warn "Running Ollama on Intel Mac — responses will be slow."
  fi
fi

# ── 6. Wait for backend ──────────────────────────────────────────────────────
section "Health check"
info "Waiting for backend..."
MAX=90; COUNT=0
until curl -sf http://localhost:8000/health >/dev/null 2>&1; do
  COUNT=$((COUNT + 1))
  [ $COUNT -ge $MAX ] && error "Backend didn't start. Run: docker compose logs backend"
  printf "."; sleep 2
done
echo " ready."

# ── 7. Seed demo data ────────────────────────────────────────────────────────
section "Seeding demo"
info "Creating MX-400 equipment and uploading manual..."

EQ_ID=$(curl -sf -X POST http://localhost:8000/api/v1/equipment/ \
  -H "Content-Type: application/json" \
  -d '{"manufacturer":"Demo Corp","model":"MX-400","equipment_type":"Motor Drive"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")

if [ -n "$EQ_ID" ]; then
  curl -sf -X POST http://localhost:8000/api/v1/documents/upload \
    -F "file=@demo-data/MX400-Maintenance-Manual-DEMO.pdf" \
    -F "title=MX-400 Maintenance Manual (DEMO)" \
    -F "equipment_id=${EQ_ID}" >/dev/null
  echo "  Equipment: MX-400 (id=${EQ_ID})"
  echo "  Manual: uploaded — ingestion running (~15s)"
else
  warn "Seeding skipped — check your API key in .env, then run: make seed"
fi

# ── 8. Done ──────────────────────────────────────────────────────────────────
section "Ready"
echo -e "${GREEN}${BOLD}Setup complete!${NC}"
echo ""
echo "  App:       http://localhost:3000"
echo "  API docs:  http://localhost:8000/docs"
echo "  Qdrant UI: http://localhost:6333/dashboard"
echo ""
echo "  Wait ~15s for manual ingestion, then open http://localhost:3000"
echo "  Ask: \"The MX-400 shows E17 after 20 minutes. What should I check?\""
echo ""
echo "  make up    start   |   make down   stop   |   make logs   logs"
echo ""

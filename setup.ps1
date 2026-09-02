#Requires -Version 7.0
# ForgeGuide AI — Windows setup (PowerShell equivalent of setup.sh)
$ErrorActionPreference = "Stop"

function Write-Info    { param($msg) Write-Host "▶ $msg" -ForegroundColor Green }
function Write-Warn    { param($msg) Write-Host "⚠  $msg" -ForegroundColor Yellow }
function Write-ErrorAndExit { param($msg) Write-Host "✗ $msg" -ForegroundColor Red; exit 1 }
function Write-Section { param($msg) Write-Host "`n$msg" -ForegroundColor Cyan; Write-Host ("─" * 39) }

function Get-EnvValue {
    param([string]$Name)
    if (-not (Test-Path .env)) { return "" }
    $line = Get-Content .env | Where-Object { $_ -match "^\s*$Name\s*=" } | Select-Object -First 1
    if (-not $line) { return "" }
    return ($line -replace "^\s*$Name\s*=", "").Trim()
}

Write-Section "ForgeGuide AI — Setup"

# ── 1. Prerequisites ─────────────────────────────────────────────────────────
Write-Info "Checking prerequisites..."

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-ErrorAndExit "Docker not found. Install Docker Desktop: https://docker.com"
}

$PythonCmd = $null
foreach ($candidate in @("py", "python", "python3")) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) { $PythonCmd = $candidate; break }
}
if (-not $PythonCmd) {
    Write-ErrorAndExit "Python 3 not found. Install: https://python.org"
}
$PythonArgs = if ($PythonCmd -eq "py") { @("-3") } else { @() }

$pyVerCheck = & $PythonCmd @PythonArgs -c "import sys; print(sys.version_info[:2] >= (3,11))"
if ($pyVerCheck.Trim() -ne "True") {
    $pyVer = & $PythonCmd @PythonArgs --version
    Write-ErrorAndExit "Python 3.11+ required (found $pyVer)"
}

try {
    docker info *> $null
} catch {
    Write-ErrorAndExit "Docker is not running. Start Docker Desktop first."
}
if ($LASTEXITCODE -ne 0) {
    Write-ErrorAndExit "Docker is not running. Start Docker Desktop first."
}

$pyVerString = (& $PythonCmd @PythonArgs --version)
$dockerVerString = (docker --version)
Write-Host "  Python: $pyVerString"
Write-Host "  Docker: $dockerVerString"
Write-Host "  OS:     Windows"

# ── 2. Environment file ──────────────────────────────────────────────────────
Write-Section "Environment"

if (-not (Test-Path .env)) {
    Copy-Item .env.example .env

    Write-Host ""
    Write-Host "  Open .env and set your API key, then press Enter."
    Write-Host ""
    Write-Host "  Option A — Anthropic (recommended):"
    Write-Host "    ANTHROPIC_API_KEY=sk-ant-..."
    Write-Host ""
    Write-Host "  Option B — OpenAI:"
    Write-Host "    LLM_PROVIDER=openai"
    Write-Host "    OPENAI_API_KEY=sk-..."
    Write-Host ""
    Write-Host "  Option C — Ollama (needs an NVIDIA GPU + WSL2 backend in Docker Desktop):"
    Write-Host "    LLM_PROVIDER=ollama"
    Write-Host ""
    Read-Host "  Press Enter after editing .env to continue"
} else {
    Write-Info ".env already exists"
}

$LlmProvider = Get-EnvValue "LLM_PROVIDER"
Write-Host "  Provider: $(if ($LlmProvider) { $LlmProvider } else { 'not set' })"

if ($LlmProvider -eq "ollama") {
    Write-Warn "LLM_PROVIDER=ollama needs an NVIDIA GPU with the Docker Desktop WSL2 backend."
    Write-Warn "Without a supported GPU, inference runs on CPU and can take 60-300s per response."
    Write-Host ""
    $confirm = Read-Host "  Continue anyway? (y/N)"
    if ($confirm -notin @("y", "Y")) {
        Write-ErrorAndExit "Change LLM_PROVIDER to anthropic or openai in .env and rerun."
    }
}

# ── 3. Demo manual ───────────────────────────────────────────────────────────
Write-Section "Demo data"

if (-not (Test-Path "demo-data/MX400-Maintenance-Manual-DEMO.pdf")) {
    Write-Info "Generating synthetic MX-400 demo manual..."
    & $PythonCmd @PythonArgs -m pip install reportlab --quiet 2>$null
    & $PythonCmd @PythonArgs scripts/generate_demo_manual.py
} else {
    Write-Info "Demo PDF already exists"
}

# ── 4. Docker services ───────────────────────────────────────────────────────
Write-Section "Docker services"
Write-Info "Building and starting services (first run: 3-5 min)..."
docker compose up -d --build
if ($LASTEXITCODE -ne 0) { Write-ErrorAndExit "docker compose up failed." }

# ── 5. Pull Ollama models (only if provider=ollama and user confirmed above) ─
if ($LlmProvider -eq "ollama") {
    Write-Section "Ollama models"

    $LlmModel = Get-EnvValue "LLM_MODEL"
    if (-not $LlmModel) { $LlmModel = "llama3.2" }
    $EmbedModel = Get-EnvValue "EMBEDDING_MODEL"
    if (-not $EmbedModel) { $EmbedModel = "nomic-embed-text" }
    $VisionModel = Get-EnvValue "OLLAMA_VISION_MODEL"

    Write-Host "  Waiting for Ollama container..." -NoNewline
    $ready = $false
    for ($i = 0; $i -lt 60; $i++) {
        try {
            Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 2 | Out-Null
            $ready = $true
            break
        } catch {
            Write-Host "." -NoNewline
            Start-Sleep -Seconds 2
        }
    }
    Write-Host ""
    if (-not $ready) { Write-ErrorAndExit "Ollama container didn't become ready." }

    Write-Info "Pulling LLM: $LlmModel"
    docker compose exec ollama ollama pull $LlmModel

    $EmbedProvider = Get-EnvValue "EMBEDDING_PROVIDER"
    if ($EmbedProvider -eq "ollama") {
        Write-Info "Pulling embed model: $EmbedModel"
        docker compose exec ollama ollama pull $EmbedModel
    }

    if ($VisionModel) {
        Write-Info "Pulling vision model: $VisionModel"
        docker compose exec ollama ollama pull $VisionModel
    }
}

# ── 6. Wait for backend ──────────────────────────────────────────────────────
Write-Section "Health check"
Write-Info "Waiting for backend..."
$max = 90
$backendReady = $false
for ($i = 0; $i -lt $max; $i++) {
    try {
        Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2 | Out-Null
        $backendReady = $true
        break
    } catch {
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 2
    }
}
if (-not $backendReady) { Write-ErrorAndExit "Backend didn't start. Run: docker compose logs backend" }
Write-Host " ready."

# ── 7. Seed demo data ────────────────────────────────────────────────────────
Write-Section "Seeding demo"
Write-Info "Creating MX-400 equipment and uploading manual..."

$eqId = $null
try {
    $body = @{ manufacturer = "Demo Corp"; model = "MX-400"; equipment_type = "Motor Drive" } | ConvertTo-Json
    $eq = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/equipment/" `
        -ContentType "application/json" -Body $body
    $eqId = $eq.id
} catch {
    $eqId = $null
}

if ($eqId) {
    try {
        Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/documents/upload" -Form @{
            file          = Get-Item "demo-data/MX400-Maintenance-Manual-DEMO.pdf"
            title         = "MX-400 Maintenance Manual (DEMO)"
            equipment_id  = "$eqId"
        } | Out-Null
        Write-Host "  Equipment: MX-400 (id=$eqId)"
        Write-Host "  Manual: uploaded — ingestion running (~15s)"
    } catch {
        Write-Warn "Manual upload failed — check your API key in .env, then run: .\make.ps1 seed"
    }
} else {
    Write-Warn "Seeding skipped — check your API key in .env, then run: .\make.ps1 seed"
}

# ── 8. Done ──────────────────────────────────────────────────────────────────
Write-Section "Ready"
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "  App:       http://localhost:3000"
Write-Host "  API docs:  http://localhost:8000/docs"
Write-Host "  Qdrant UI: http://localhost:6333/dashboard"
Write-Host ""
Write-Host "  Wait ~15s for manual ingestion, then open http://localhost:3000"
Write-Host "  Ask: `"The MX-400 shows E17 after 20 minutes. What should I check?`""
Write-Host ""
Write-Host "  .\make.ps1 up    start   |   .\make.ps1 down   stop   |   .\make.ps1 logs   logs"
Write-Host ""

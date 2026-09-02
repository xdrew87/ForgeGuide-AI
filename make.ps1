# ForgeGuide AI - Windows task runner (PowerShell equivalent of the Makefile)
# Works on both Windows PowerShell 5.1 (built into Windows) and PowerShell 7+.
# Pure ASCII on purpose: Windows PowerShell 5.1 does not reliably auto-detect
# UTF-8 without a BOM, and misreading non-ASCII bytes breaks parsing.
#
# Usage: .\make.ps1 <target> [-Model <name>]
# Example: .\make.ps1 ollama-pull-llm -Model mistral
param(
    [Parameter(Position = 0)]
    [string]$Target = "help",

    [string]$Model
)

$ErrorActionPreference = "Stop"

function Get-PythonCmd {
    foreach ($candidate in @("py", "python", "python3")) {
        if (Get-Command $candidate -ErrorAction SilentlyContinue) {
            if ($candidate -eq "py") {
                return [PSCustomObject]@{ Exe = "py"; Args = @("-3") }
            }
            return [PSCustomObject]@{ Exe = $candidate; Args = @() }
        }
    }
    throw "Python 3 not found. Install: https://python.org"
}

switch ($Target) {

    "setup" {
        & "$PSScriptRoot\setup.ps1"
    }

    "up" {
        docker compose up -d
    }

    "rebuild" {
        docker compose up -d --build
    }

    "down" {
        docker compose down
    }

    "logs" {
        docker compose logs -f
    }

    "logs-backend" {
        docker compose logs -f backend
    }

    "test" {
        Push-Location backend
        try {
            python -m pytest tests/ -v
        } finally {
            Pop-Location
        }
    }

    "demo" {
        $py = Get-PythonCmd
        $pyArgs = $py.Args
        & $py.Exe @pyArgs scripts/generate_demo_manual.py
    }

    "seed" {
        Write-Host "Seeding demo data..."
        $body = @{ manufacturer = "Demo Corp"; model = "MX-400"; equipment_type = "Motor Drive" } | ConvertTo-Json
        $eq = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/equipment/" `
            -ContentType "application/json" -Body $body
        $eqId = $eq.id
        & curl.exe -sf -X POST "http://localhost:8000/api/v1/documents/upload" `
            -F "file=@demo-data/MX400-Maintenance-Manual-DEMO.pdf" `
            -F "title=MX-400 Maintenance Manual (DEMO)" `
            -F "equipment_id=$eqId" | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Document upload failed (curl exit $LASTEXITCODE)" }
        Write-Host "Done. Equipment id: $eqId"
    }

    "clean" {
        docker compose down -v
        Write-Host "All volumes removed."
    }

    "urls" {
        Write-Host "App:        http://localhost:3000"
        Write-Host "API docs:   http://localhost:8000/docs"
        Write-Host "Qdrant UI:  http://localhost:6333/dashboard"
        Write-Host "Ollama:     http://localhost:11434"
    }

    "ollama-pull-llm" {
        $m = if ($Model) { $Model } else { "llama3.2" }
        docker compose exec ollama ollama pull $m
    }

    "ollama-pull-embed" {
        $m = if ($Model) { $Model } else { "nomic-embed-text" }
        docker compose exec ollama ollama pull $m
    }

    "ollama-pull-vision" {
        $m = if ($Model) { $Model } else { "llava" }
        docker compose exec ollama ollama pull $m
    }

    "ollama-list" {
        docker compose exec ollama ollama list
    }

    "ollama-run" {
        $m = if ($Model) { $Model } else { "llama3.2" }
        docker compose exec -it ollama ollama run $m
    }

    default {
        Write-Host "ForgeGuide AI - available targets:"
        Write-Host ""
        Write-Host "  setup                start-to-finish setup (env, demo PDF, docker, seed)"
        Write-Host "  up                    start all services"
        Write-Host "  rebuild               rebuild images and start (after code changes)"
        Write-Host "  down                  stop all services"
        Write-Host "  logs                  tail all service logs"
        Write-Host "  logs-backend          tail backend logs only"
        Write-Host "  test                  run the backend test suite"
        Write-Host "  demo                  generate the synthetic demo PDF"
        Write-Host "  seed                  create demo equipment + upload the demo manual"
        Write-Host "  clean                 stop and wipe all volumes (full reset)"
        Write-Host "  urls                  print service URLs"
        Write-Host "  ollama-pull-llm       pull the configured LLM (-Model to override)"
        Write-Host "  ollama-pull-embed     pull a recommended embedding model"
        Write-Host "  ollama-pull-vision    pull a recommended vision model (llava)"
        Write-Host "  ollama-list           list downloaded Ollama models"
        Write-Host "  ollama-run            interactive shell against the configured model"
        Write-Host ""
        Write-Host "Usage: .\make.ps1 <target> [-Model <name>]"
    }
}

# AgenticOS — boot the durable core stack (Windows PowerShell 7+)
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "[setup] Created deploy\.env from template."
    Write-Host "[setup] EDIT IT (ANTHROPIC_API_KEY, MINIMAX_API_KEY, LITELLM_MASTER_KEY, POSTGRES_PASSWORD) then re-run setup."
    exit 2
}

try { docker info | Out-Null }
catch { Write-Host "[setup] Docker Desktop is not running (or not installed). See HANDOFF.md step 1."; exit 1 }

Write-Host "[setup] booting core stack (postgres, redis, temporal, temporal-ui, litellm)..."
docker compose up -d --wait postgres redis temporal temporal-ui litellm
if ($LASTEXITCODE -ne 0) { Write-Host "[setup] compose up failed — check 'docker compose ps'"; exit 1 }

Write-Host "[setup] registering Temporal namespace 'agentos' (idempotent)..."
docker compose --profile setup run --rm temporal-ns 2>$null | Out-Null

Write-Host ""
Write-Host "[setup] core stack UP. Now verify:"
Write-Host "        pwsh scripts\verify.ps1          # + -Full for all model groups"
Write-Host ""
Write-Host "[setup] optional free-local fallback: docker compose --profile local up -d ollama"
Write-Host "        then: docker compose exec ollama ollama pull qwen3:8b"
Write-Host "[setup] optional n8n integrations:   docker compose --profile integrations up -d n8n"

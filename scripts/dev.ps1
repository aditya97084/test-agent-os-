# AgenticOS Phase-0 dev run WITHOUT docker (local engine + sqlite).
# For the durable path: deploy\scripts\setup.ps1 then AGENTOS_ENGINE=temporal.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
$py = "python"
foreach ($c in @("python", "python3", "py")) { $g = Get-Command $c -ErrorAction SilentlyContinue; if ($g) { $py = $g.Source; break } }
& $py -m pip install -q -e . | Out-Null
New-Item -ItemType Directory -Force data, logs | Out-Null
$env:AGENTOS_ROOT = (Get-Location).Path
$env:AGENTOS_ENGINE = "local"
if (-not $env:GATEWAY_PORT) { $env:GATEWAY_PORT = "8000" }
if (-not $env:DEMO_STEP_SECONDS) { $env:DEMO_STEP_SECONDS = "5" }
if (-not $env:AGENTOS_DB_URL) { $env:AGENTOS_DB_URL = "sqlite+aiosqlite://$($PWD.Path)/data/dev.db" }
Write-Host "[dev] gateway on :$env:GATEWAY_PORT — engine=local(dev), DB=$env:AGENTOS_DB_URL"
& $py -m agentos_gateway

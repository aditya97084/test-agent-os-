# AgenticOS — verify infra + LIVE model routing. Usage: pwsh verify.ps1 [-Full]
param([switch]$Full)
$ErrorActionPreference = "Stop"
$py = $null
foreach ($c in @("python", "python3", "py")) {
    $found = Get-Command $c -ErrorAction SilentlyContinue
    if ($found) { $py = $found.Source; break }
}
if (-not $py) { Write-Host "[verify] Python 3.10+ not found. Install: winget install Python.Python.3.12"; exit 1 }
$args = @()
if ($Full) { $args += "--full" }
& $py "$PSScriptRoot\smoke_verify.py" @args
exit $LASTEXITCODE

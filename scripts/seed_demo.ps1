# Seed demo artifacts locally
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..
conda activate nexus
python scripts/run_investor_demo.py
Write-Host "Demo seed complete. Start API with: uvicorn nexus.entrypoints.api:app --port 8000"
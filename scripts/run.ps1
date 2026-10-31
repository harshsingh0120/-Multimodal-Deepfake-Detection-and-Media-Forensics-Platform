# One-command run (Windows PowerShell): build the frontend and serve everything
# from the FastAPI backend at http://localhost:8000
# Usage:  ./scripts/run.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# 1. Backend venv + deps
if (-not (Test-Path ".venv")) {
  Write-Host "Creating virtual environment..." -ForegroundColor Cyan
  py -3.12 -m venv .venv
}
Write-Host "Installing backend dependencies..." -ForegroundColor Cyan
& .\.venv\Scripts\python.exe -m pip install --quiet --upgrade pip
& .\.venv\Scripts\python.exe -m pip install --quiet -r backend\requirements.txt

# 2. Build frontend
Write-Host "Building frontend..." -ForegroundColor Cyan
Set-Location frontend
npm install
npm run build
Set-Location $root

# 3. Run backend (serves the built frontend)
Write-Host "Starting server at http://localhost:8000 ..." -ForegroundColor Green
Set-Location backend
& ..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000

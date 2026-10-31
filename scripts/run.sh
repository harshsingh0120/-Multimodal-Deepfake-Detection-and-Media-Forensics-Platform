#!/usr/bin/env bash
# One-command run (Linux/macOS): build the frontend and serve everything
# from the FastAPI backend at http://localhost:8000
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# 1. Backend venv + deps
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi
echo "Installing backend dependencies..."
./.venv/bin/python -m pip install --quiet --upgrade pip
./.venv/bin/python -m pip install --quiet -r backend/requirements.txt

# 2. Build frontend
echo "Building frontend..."
cd frontend
npm install
npm run build
cd "$ROOT"

# 3. Run backend (serves the built frontend)
echo "Starting server at http://localhost:8000 ..."
cd backend
exec ../.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

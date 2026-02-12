#!/bin/bash

# Avvia backend e frontend in parallelo.
# Ctrl+C termina entrambi i processi.

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

cleanup() {
  echo ""
  echo "Arresto dei servizi..."
  kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
  wait $BACKEND_PID $FRONTEND_PID 2>/dev/null
  echo "Servizi arrestati."
}

trap cleanup EXIT INT TERM

# Avvia PostgreSQL 16 (se non già attivo)
if ! /opt/homebrew/opt/postgresql@16/bin/pg_isready -p 5433 -q 2>/dev/null; then
  echo "Avvio PostgreSQL@16 su porta 5433..."
  /opt/homebrew/opt/postgresql@16/bin/pg_ctl -D /opt/homebrew/var/postgresql@16 -o "-p 5433" -l /opt/homebrew/var/log/postgresql@16.log start
fi

# Backend
echo "Avvio backend (FastAPI) su http://localhost:8000 ..."
cd "$ROOT_DIR/backend"
source "$ROOT_DIR/.venv/bin/activate"
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

# Frontend
echo "Avvio frontend (Next.js) su http://localhost:3000 ..."
cd "$ROOT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "=== Gestionale Tesoreria ==="
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000"
echo "Swagger:  http://localhost:8000/docs"
echo "==========================="
echo ""

wait

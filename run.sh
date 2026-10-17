#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "== Secure Health Data - inicializando =="

PYTHON=".venv/bin/python"

if [ ! -x "$PYTHON" ]; then
  if command -v uv >/dev/null 2>&1; then
    uv sync
  else
    python3 -m venv .venv
    "$PYTHON" -m pip install --upgrade pip
    "$PYTHON" -m pip install -r requirements.txt
  fi
fi

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Arquivo .env criado a partir do .env.example — preencha LLM_BASE_URL e OLLAMA_API_KEY."
fi

echo "Populando banco (seed)..."
"$PYTHON" scripts/seed.py

echo "Iniciando API + interface em http://localhost:8000"
"$PYTHON" -m uvicorn app.main:app --host 0.0.0.0 --port 8000

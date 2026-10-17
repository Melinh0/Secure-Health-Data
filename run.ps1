$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "== Secure Health Data - inicializando ==" -ForegroundColor Cyan

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "Criando ambiente virtual..."
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        uv sync
    } else {
        python -m venv .venv
        & $python -m pip install --upgrade pip
        & $python -m pip install -r requirements.txt
    }
}

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Arquivo .env criado a partir do .env.example. Preencha LLM_BASE_URL e OLLAMA_API_KEY."
}

Write-Host "Populando banco (seed)..."
& $python scripts\seed.py

Write-Host "Iniciando API + interface em http://localhost:8000" -ForegroundColor Green
& $python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .database import init_db
from .rag import RAGManager
from .routers import analise, exames, pacientes, prontuario, sistema

logging.basicConfig(level=logging.INFO)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    app.state.rag = RAGManager()
    logging.info("API iniciada em %s", FRONTEND_DIR)
    yield


app = FastAPI(
    title="Secure Health Data",
    description="Análise clínica com IA: exames, tendências, alertas, RAG e prontuário SOAP",
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(sistema.router)
app.include_router(pacientes.router)
app.include_router(exames.router)
app.include_router(analise.router)
app.include_router(prontuario.router)

app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

from fastapi import APIRouter

from ..config import settings

router = APIRouter(prefix="/api", tags=["sistema"])

VERSION = "2.0.0"


@router.get("/health")
def health():
    return {"status": "ok", "version": VERSION}


@router.get("/config")
def config():
    return {
        "llm_configured": settings.llm_configured,
        "llm_model": settings.llm_model,
        "available_models": settings.available_models,
        "clinical_alerts_enabled": settings.clinical_alerts_enabled,
        "version": VERSION,
    }

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import UploadResponse
from ..services.exames import processar_csv_exames

router = APIRouter(prefix="/api", tags=["exames"])


@router.post("/upload_exame", response_model=UploadResponse)
async def upload_exame(
    file: UploadFile = File(...),
    paciente_id: int | None = Form(None),
    db: Session = Depends(get_db),
):
    conteudo = await file.read()
    return processar_csv_exames(conteudo, db, paciente_id)

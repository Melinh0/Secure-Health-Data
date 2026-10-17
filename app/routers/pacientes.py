from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import PacienteDetalhe, PacienteResumo
from ..services import pacientes as svc

router = APIRouter(prefix="/api/pacientes", tags=["pacientes"])


@router.get("", response_model=list[PacienteResumo])
def listar(db: Session = Depends(get_db)):
    return svc.listar_pacientes(db)


@router.get("/{paciente_id}", response_model=PacienteDetalhe)
def obter(paciente_id: int, db: Session = Depends(get_db)):
    paciente = svc.obter_paciente(db, paciente_id)
    if not paciente:
        raise HTTPException(404, "Paciente não encontrado")
    return {
        "id": paciente.id,
        "nome_anon": paciente.nome_anon,
        "data_nascimento": paciente.data_nascimento,
        "sexo": paciente.sexo,
        "idade_aprox": svc.calcular_idade(paciente.data_nascimento),
        "exames": svc.carregar_exames_paciente(paciente_id, db),
        "anotacoes": svc.carregar_anotacoes_paciente(paciente_id, db),
    }

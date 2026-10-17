from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AnotacaoClinica
from ..schemas import ProntuarioRequest, ProntuarioResponse
from ..services import pacientes as svc
from ..services.analise import detectar_mudancas_significativas
from ..services.prontuario import gerar_prontuario_soap

router = APIRouter(prefix="/api", tags=["prontuario"])


@router.post("/gerar_prontuario", response_model=ProntuarioResponse)
def gerar_prontuario(req: ProntuarioRequest, request: Request, db: Session = Depends(get_db)):
    paciente = svc.obter_paciente(db, req.paciente_id)
    if not paciente:
        raise HTTPException(404, "Paciente não encontrado")

    exames = svc.carregar_exames_paciente(req.paciente_id, db)
    anotacoes = svc.carregar_anotacoes_paciente(req.paciente_id, db)
    medicamentos = svc.parse_medicamentos(req.medicamentos_atual) or svc.obter_medicamentos_ativos(req.paciente_id, db)

    tendencias = detectar_mudancas_significativas(svc.agrupar_exames_por_tipo(exames))

    literatura = request.app.state.rag.recuperar_literatura(
        " ".join(f"{tipo}: {e.get('ultimo_valor', '')}" for tipo, e in tendencias.items()),
        top_k=2,
    )

    prontuario = gerar_prontuario_soap(
        paciente_info={"nome_anon": paciente.nome_anon, "idade_aprox": svc.calcular_idade(paciente.data_nascimento)},
        exames=exames,
        anotacoes=anotacoes,
        analise_tendencias=tendencias,
        contexto_literatura=literatura,
        conduta_medica=req.conduta_medica,
        observacoes_medico=req.observacoes_medico,
        medicamentos=medicamentos,
    )

    nova_anotacao = AnotacaoClinica(
        paciente_id=req.paciente_id,
        data=datetime.now(),
        texto=f"Conduta: {req.conduta_medica}\nObservações: {req.observacoes_medico}",
        tipo="evolucao",
    )
    db.add(nova_anotacao)
    db.commit()
    db.refresh(nova_anotacao)

    request.app.state.rag.indexar_anotacoes_paciente(req.paciente_id, [{
        "data": nova_anotacao.data,
        "texto": nova_anotacao.texto,
        "tipo": nova_anotacao.tipo,
    }])

    return {"prontuario": prontuario}

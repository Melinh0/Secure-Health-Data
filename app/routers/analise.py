import json

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..llm import LLMError, chamar_llm
from ..schemas import AnaliseRequest, AnaliseResponse
from ..services import pacientes as svc
from ..services.alertas import verificar_alertas_criticos
from ..services.analise import detectar_mudancas_significativas

router = APIRouter(prefix="/api", tags=["analise"])

SYSTEM_PROMPT = (
    "Você é um assistente em psiquiatria. Forneça análise clínica baseada em evidências, "
    "destacando correlações entre exames e sintomas, e sugerindo condutas seguras. "
    "Sempre lembre que o médico deve validar."
)


def _montar_query(tendencias: dict, observacoes: str | None) -> str:
    partes = [
        f"{tipo}: {estat.get('ultimo_valor', '')} {estat.get('tendencia_direcao', '')}"
        for tipo, estat in tendencias.items()
    ]
    if observacoes:
        partes.append(observacoes)
    return " ".join(partes)


@router.post("/analisar", response_model=AnaliseResponse)
def analisar(req: AnaliseRequest, request: Request, db: Session = Depends(get_db)):
    paciente = svc.obter_paciente(db, req.paciente_id)
    if not paciente:
        raise HTTPException(404, "Paciente não encontrado")

    exames = svc.carregar_exames_paciente(req.paciente_id, db)
    if not exames:
        raise HTTPException(404, "Paciente sem exames registrados")

    anotacoes = svc.carregar_anotacoes_paciente(req.paciente_id, db)
    medicamentos = svc.parse_medicamentos(req.medicamentos_atual) or svc.obter_medicamentos_ativos(req.paciente_id, db)

    por_tipo = svc.agrupar_exames_por_tipo(exames)
    tendencias = detectar_mudancas_significativas(por_tipo)

    alertas = []
    if settings.clinical_alerts_enabled:
        alertas = verificar_alertas_criticos({"nome_anon": paciente.nome_anon}, exames, medicamentos)

    serie_temporal = {
        tipo: [
            {"data": e["data_coleta"].isoformat(), "valor": e["valor"]}
            for e in lista
        ]
        for tipo, lista in por_tipo.items()
    }

    literatura = request.app.state.rag.recuperar_literatura(
        _montar_query(tendencias, req.observacoes_medico), top_k=3
    )

    user_prompt = f"""
Dados do paciente (ID: {req.paciente_id}):
- Anotações: {[a['texto'] for a in anotacoes[-3:]]}
- Medicamentos: {medicamentos}
- Tendências laboratoriais: {json.dumps(tendencias, indent=2, default=str)}
- Observações do médico: {req.observacoes_medico or "Nenhuma"}
- Alertas automáticos: {json.dumps(alertas, indent=2, default=str)}

Literatura relevante:
{chr(10).join(literatura)}

Com base nesses dados, forneça:
1. Uma interpretação resumida das tendências dos exames (destaque anormalidades).
2. Correlações com possíveis condições psiquiátricas (ex: TSH alto e depressão).
3. Sugestões de intervenção (medicamentosas ou não) baseadas em evidências.
4. Recomendações para outros profissionais (nutrição, psicologia).

Mantenha o tom profissional e claro.
"""

    analise_llm = None
    erro_llm = None
    try:
        analise_llm = chamar_llm(user_prompt, system_message=SYSTEM_PROMPT, model=req.modelo)
    except LLMError as erro:
        erro_llm = str(erro)

    return {
        "paciente_id": req.paciente_id,
        "tendencias": tendencias,
        "alertas": alertas,
        "serie_temporal": serie_temporal,
        "literatura_usada": literatura,
        "analise_llm": analise_llm,
        "erro_llm": erro_llm,
    }

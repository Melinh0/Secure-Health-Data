from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from ..models import AnotacaoClinica, Exame, Paciente

COLUNAS_EXAMES = [
    "hemoglobina_g_dL", "eritrocitos_milhoes_uL", "leucocitos_mm3", "plaquetas_mm3",
    "colesterol_total_mg_dL", "triglicerides_mg_dL", "glicose_mg_dL", "creatinina_mg_dL",
    "vitamina_B12_pg_mL", "vitamina_D_ng_mL", "TGO_AST_U_L", "TGP_ALT_U_L", "GGT_U_L",
    "TSH_mIU_L", "T4_livre_ng_dL", "troponina_T_ng_mL",
]

MEDICAMENTOS_CONHECIDOS = [
    "lítio", "lithium", "clozapina", "risperidona", "olanzapina", "aripiprazol",
    "fluoxetina", "sertralina", "escitalopram", "venlafaxina", "bupropiona",
    "tranilcipromina", "fenelzina", "haloperidol",
]


def carregar_exames_paciente(paciente_id: int, db: Session) -> list[dict]:
    exames = (
        db.query(Exame)
        .filter(Exame.paciente_id == paciente_id)
        .order_by(Exame.data_coleta)
        .all()
    )
    return [
        {
            "id": e.id,
            "data_coleta": e.data_coleta,
            "exame_nome": e.exame_nome,
            "valor": e.valor,
            "unidade": e.unidade,
            "referencia_min": e.referencia_min,
            "referencia_max": e.referencia_max,
        }
        for e in exames
    ]


def agrupar_exames_por_tipo(exames: list[dict]) -> dict[str, list[dict]]:
    agrupados: dict[str, list[dict]] = {}
    for e in exames:
        agrupados.setdefault(e["exame_nome"], []).append(e)
    return agrupados


def carregar_anotacoes_paciente(paciente_id: int, db: Session) -> list[dict]:
    anotacoes = (
        db.query(AnotacaoClinica)
        .filter(AnotacaoClinica.paciente_id == paciente_id)
        .order_by(AnotacaoClinica.data)
        .all()
    )
    return [{"id": a.id, "data": a.data, "texto": a.texto, "tipo": a.tipo} for a in anotacoes]


def obter_medicamentos_ativos(paciente_id: int, db: Session) -> list[str]:
    anotacoes = (
        db.query(AnotacaoClinica)
        .filter(
            AnotacaoClinica.paciente_id == paciente_id,
            AnotacaoClinica.tipo == "prescricao",
        )
        .order_by(AnotacaoClinica.data.desc())
        .all()
    )
    medicamentos = set()
    for a in anotacoes:
        texto = a.texto.lower()
        for nome in MEDICAMENTOS_CONHECIDOS:
            if nome in texto:
                medicamentos.add(nome)
    return sorted(medicamentos)


def parse_medicamentos(texto: str | None) -> list[str] | None:
    if not texto:
        return None
    return [m.strip() for m in texto.split(",") if m.strip()]


def listar_pacientes(db: Session) -> list[dict[str, Any]]:
    pacientes = db.query(Paciente).order_by(Paciente.id).all()
    return [
        {
            "id": p.id,
            "nome_anon": p.nome_anon,
            "sexo": p.sexo,
            "total_exames": db.query(Exame).filter(Exame.paciente_id == p.id).count(),
            "total_anotacoes": db.query(AnotacaoClinica).filter(AnotacaoClinica.paciente_id == p.id).count(),
        }
        for p in pacientes
    ]


def obter_paciente(db: Session, paciente_id: int) -> Paciente | None:
    return db.query(Paciente).filter(Paciente.id == paciente_id).first()


def calcular_idade(data_nascimento: Any) -> str:
    if not data_nascimento:
        return "?"
    try:
        ano = int(str(data_nascimento)[:4])
        return str(max(datetime.now().year - ano, 0))
    except (ValueError, TypeError):
        return "?"

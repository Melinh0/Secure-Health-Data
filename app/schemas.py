from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ExameOut(BaseModel):
    id: int
    data_coleta: datetime
    exame_nome: str
    valor: float
    unidade: str | None = None
    referencia_min: float | None = None
    referencia_max: float | None = None


class AnotacaoOut(BaseModel):
    id: int
    data: datetime
    texto: str
    tipo: str | None = None


class PacienteResumo(BaseModel):
    id: int
    nome_anon: str
    sexo: str | None = None
    total_exames: int = 0
    total_anotacoes: int = 0


class PacienteDetalhe(BaseModel):
    id: int
    nome_anon: str
    data_nascimento: datetime | None = None
    sexo: str | None = None
    idade_aprox: str = "?"
    exames: list[ExameOut] = []
    anotacoes: list[AnotacaoOut] = []


class AnaliseRequest(BaseModel):
    paciente_id: int
    observacoes_medico: str | None = None
    medicamentos_atual: str | None = None
    modelo: str | None = None


class AnaliseResponse(BaseModel):
    paciente_id: int
    tendencias: dict[str, Any] = {}
    alertas: list[dict[str, Any]] = []
    serie_temporal: dict[str, list[dict[str, Any]]] = {}
    literatura_usada: list[str] = []
    analise_llm: str | None = None
    erro_llm: str | None = None


class ProntuarioRequest(BaseModel):
    paciente_id: int
    conduta_medica: str
    observacoes_medico: str
    medicamentos_atual: str | None = None


class ProntuarioResponse(BaseModel):
    prontuario: str


class UploadResponse(BaseModel):
    message: str
    paciente_id: int
    exames_inseridos: int


class SistemaConfig(BaseModel):
    llm_configured: bool
    llm_model: str
    available_models: list[str]
    clinical_alerts_enabled: bool
    version: str

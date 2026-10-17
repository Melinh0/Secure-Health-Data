import io
from datetime import datetime

import pandas as pd
from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import AnotacaoClinica, Exame, Paciente
from .anonimizacao import anonimizar_dados
from .pacientes import COLUNAS_EXAMES


def processar_csv_exames(conteudo: bytes, db: Session, paciente_id: int | None = None) -> dict:
    try:
        df = pd.read_csv(io.StringIO(conteudo.decode("utf-8-sig")))
    except Exception:
        raise HTTPException(400, "Arquivo inválido: esperado um CSV legível")

    if df.empty:
        raise HTTPException(400, "Arquivo vazio")

    dados_anon = anonimizar_dados(df.iloc[0].to_dict())

    paciente = None
    if paciente_id:
        paciente = db.query(Paciente).filter(Paciente.id == paciente_id).first()
        if not paciente:
            raise HTTPException(404, "Paciente não encontrado")
    else:
        nome_anon = dados_anon.get("nome_completo")
        if nome_anon:
            paciente = db.query(Paciente).filter(Paciente.nome_anon == nome_anon).first()

    if not paciente:
        paciente = Paciente(
            nome_anon=dados_anon.get("nome_completo") or "Paciente_Desconhecido",
            data_nascimento=_parse_nascimento(dados_anon.get("data_nascimento")),
            sexo=dados_anon.get("sexo"),
        )
        db.add(paciente)
        db.commit()
        db.refresh(paciente)

    data_coleta = _parse_data(dados_anon.get("cadastro")) or datetime.now()

    inseridos = 0
    for col in COLUNAS_EXAMES:
        valor = para_valor_exame(dados_anon.get(col))
        if valor is not None:
            db.add(Exame(
                paciente_id=paciente.id,
                data_coleta=data_coleta,
                exame_nome=col,
                valor=valor,
                unidade="",
            ))
            inseridos += 1

    ecg = dados_anon.get("eletrocardiograma_ECG")
    if ecg is not None and not pd.isna(ecg):
        db.add(AnotacaoClinica(
            paciente_id=paciente.id,
            data=data_coleta,
            texto=f"ECG: {ecg}",
            tipo="exame",
        ))

    db.commit()
    return {"message": "Exames processados", "paciente_id": paciente.id, "exames_inseridos": inseridos}


def _parse_data(valor) -> datetime | None:
    if valor is None or pd.isna(valor):
        return None
    try:
        return pd.to_datetime(valor, dayfirst=True).to_pydatetime()
    except Exception:
        return None


CATEGORICOS = {
    "norm": 95.0,
    "normal": 95.0,
    ">300": 310.0,
    ">200": 210.0,
}


def para_valor_exame(valor) -> float | None:
    numero = _para_float(valor)
    if numero is not None:
        return numero
    if valor is None:
        return None
    return CATEGORICOS.get(str(valor).strip().lower())


def _para_float(valor) -> float | None:
    try:
        numero = pd.to_numeric(valor, errors="coerce")
    except Exception:
        return None
    if numero is None or pd.isna(numero):
        return None
    return float(numero)


def _parse_nascimento(valor) -> datetime | None:
    if valor is None or pd.isna(valor):
        return None
    texto = str(valor).strip()
    if len(texto) == 4 and texto.isdigit():
        return datetime(int(texto), 1, 1)
    convertido = _parse_data(valor)
    if convertido:
        return datetime(convertido.year, 1, 1)
    return None

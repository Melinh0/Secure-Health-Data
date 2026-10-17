import hashlib
from datetime import datetime
from typing import Any


def anonimizar_dados(dados: dict[str, Any]) -> dict[str, Any]:
    dados_anon = dados.copy()

    if "nome_completo" in dados_anon and dados_anon["nome_completo"] is not None:
        dados_anon["nome_completo"] = gerar_nome_anon(str(dados_anon["nome_completo"]))

    for chave in ("cpf", "CPF", "endereco", "logradouro", "bairro", "cidade", "telefone", "email"):
        dados_anon.pop(chave, None)

    if "data_nascimento" in dados_anon:
        try:
            dt = datetime.strptime(str(dados_anon["data_nascimento"]), "%d/%m/%Y")
            dados_anon["data_nascimento"] = dt.strftime("%Y")
        except ValueError:
            dados_anon.pop("data_nascimento", None)

    return dados_anon


def gerar_nome_anon(nome: str) -> str:
    return f"Paciente_{hashlib.sha256(nome.encode()).hexdigest()[:8]}"

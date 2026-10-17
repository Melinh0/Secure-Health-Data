from datetime import datetime
from typing import Any

from .alertas import verificar_alertas_criticos


def gerar_prontuario_soap(
    paciente_info: dict[str, Any],
    exames: list[dict],
    anotacoes: list[dict],
    analise_tendencias: dict[str, Any],
    contexto_literatura: list[str],
    conduta_medica: str,
    observacoes_medico: str,
    medicamentos: list[str] | None = None,
) -> str:
    data_atual = datetime.now().strftime("%d/%m/%Y")
    partes = [
        f"**PRONTUÁRIO - {data_atual}**\n",
        f"Paciente: {paciente_info.get('nome_anon', 'Não identificado')}\n",
        f"Idade aproximada: {paciente_info.get('idade_aprox', '?')} anos\n\n",
        "**Subjetivo (S)**\n",
    ]

    if anotacoes:
        partes.append(f"{anotacoes[-1].get('texto', '')}\n")
    partes.append(f"Observações do médico: {observacoes_medico}\n\n")

    partes.append("**Objetivo (O)**\n")
    for tipo, estat in analise_tendencias.items():
        linha = f"- {tipo}: último = {estat['ultimo_valor']:.2f} (variação {estat['delta_percentual']:.1f}% no período). "
        if estat.get("significativa"):
            linha += f"Tendência significativa ({estat['tendencia_direcao']})."
        partes.append(linha + "\n")
    partes.append("\n")

    alertas = verificar_alertas_criticos(paciente_info, exames, medicamentos)
    if alertas:
        partes.append("**⚠️ ALERTAS DE SEGURANÇA**\n")
        for al in alertas:
            partes.append(f"- **{al['titulo']}**: {al['mensagem']}\n")
            partes.append(f"  - Recomendação: {al['recomendacao']}\n")
        partes.append("\n")

    partes.append("**Avaliação (A)**\n")
    if contexto_literatura:
        partes.append("Baseado na literatura psiquiátrica:\n")
        for ref in contexto_literatura[:2]:
            partes.append(f"- {ref[:200]}...\n")
        partes.append("\n")
    partes.append("Interpretação: os dados laboratoriais sugerem... [a ser completado pelo médico]\n\n")

    partes.append("**Plano (P)**\n")
    partes.append(conduta_medica + "\n\n")
    partes.append("---\n")
    partes.append("*Este prontuário foi gerado com auxílio de IA e deve ser revisado e validado pelo profissional responsável.*")

    return "\n".join(partes)

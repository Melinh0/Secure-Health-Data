from typing import Any

IMAO = ("tranilcipromina", "fenelzina", "moclobemida")
ISRS = ("fluoxetina", "sertralina", "escitalopram", "paroxetina", "citalopram")


def _agrupar(exames: list[dict]) -> dict[str, list[dict]]:
    agrupados: dict[str, list[dict]] = {}
    for e in exames:
        agrupados.setdefault(e["exame_nome"], []).append(e)
    return agrupados


def _alerta(tipo: str, titulo: str, mensagem: str, recomendacao: str) -> dict[str, str]:
    return {"tipo": tipo, "titulo": titulo, "mensagem": mensagem, "recomendacao": recomendacao}


def verificar_alertas_criticos(
    paciente_info: dict[str, Any],
    exames: list[dict],
    medicamentos: list[str] | None = None,
) -> list[dict[str, Any]]:
    if not exames:
        return []

    alertas: list[dict[str, Any]] = []
    por_tipo = _agrupar(exames)

    if "leucocitos_mm3" in por_tipo and por_tipo["leucocitos_mm3"][-1]["valor"] < 3000:
        alertas.append(_alerta(
            "alta_prioridade",
            "Risco de Agranulocitose",
            "Leucócitos baixos (< 3000). Se o paciente estiver em uso de Clozapina, suspender imediatamente e realizar hemograma com contagem de neutrófilos.",
            "Suspender Clozapina até confirmação. Encaminhar para hematologia.",
        ))

    if "triglicerides_mg_dL" in por_tipo and "glicose_mg_dL" in por_tipo:
        trig = por_tipo["triglicerides_mg_dL"][-1]["valor"]
        gli = por_tipo["glicose_mg_dL"][-1]["valor"]
        if trig > 150 or gli > 100:
            alertas.append(_alerta(
                "media_prioridade",
                "Síndrome Metabólica em risco",
                f"Alterações metabólicas (triglicérides {trig:.0f} mg/dL, glicose {gli:.0f} mg/dL). Associado a antipsicóticos, pode indicar síndrome metabólica.",
                "Monitorar perfil lipídico, glicemia de jejum, peso e circunferência abdominal.",
            ))

    if "creatinina_mg_dL" in por_tipo:
        creat = por_tipo["creatinina_mg_dL"][-1]["valor"]
        if creat > 1.5:
            alertas.append(_alerta(
                "alta_prioridade",
                "Risco de Nefrotoxicidade por Lítio",
                f"Creatinina elevada ({creat:.2f} mg/dL). Pode indicar nefropatia intersticial em paciente em uso de lítio.",
                "Avaliar função renal, dosar litemia, considerar suspensão do lítio.",
            ))

    if "vitamina_D_ng_mL" in por_tipo:
        vit_d = por_tipo["vitamina_D_ng_mL"][-1]["valor"]
        if vit_d < 30:
            alertas.append(_alerta(
                "baixa_prioridade",
                "Deficiência de Vitamina D",
                f"Vitamina D = {vit_d:.1f} ng/mL (normal > 30). Pode contribuir para sintomas depressivos, fadiga e dor.",
                "Suplementação de vitamina D e exposição solar. Reavaliar em 3 meses.",
            ))

    if "vitamina_B12_pg_mL" in por_tipo:
        vit_b12 = por_tipo["vitamina_B12_pg_mL"][-1]["valor"]
        if vit_b12 < 200:
            alertas.append(_alerta(
                "media_prioridade",
                "Deficiência de Vitamina B12",
                f"Vitamina B12 = {vit_b12:.0f} pg/mL (normal > 200). Pode causar declínio cognitivo, neuropatia e sintomas depressivos.",
                "Reposição de B12 (IM ou oral). Investigar causas de má absorção.",
            ))

    if medicamentos:
        tem_imao = any(any(nome in m.lower() for nome in IMAO) for m in medicamentos)
        tem_isrs = any(any(nome in m.lower() for nome in ISRS) for m in medicamentos)
        if tem_imao and tem_isrs:
            alertas.append(_alerta(
                "alta_prioridade",
                "Risco de Síndrome Serotoninérgica",
                "Combinação de IMAO e ISRS está contraindicada. Risco de síndrome serotoninérgica fatal.",
                "Suspender IMAO e aguardar washout de 14 dias antes de iniciar ISRS.",
            ))

    return alertas

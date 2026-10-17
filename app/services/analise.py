from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

REFERENCIAS = {
    "hemoglobina_g_dL": (12.0, 16.0),
    "colesterol_total_mg_dL": (150, 200),
    "triglicerides_mg_dL": (0, 150),
    "glicose_mg_dL": (70, 100),
    "creatinina_mg_dL": (0.6, 1.2),
    "vitamina_B12_pg_mL": (200, 900),
    "vitamina_D_ng_mL": (30, 100),
    "TGO_AST_U_L": (0, 40),
    "TGP_ALT_U_L": (0, 40),
    "GGT_U_L": (8, 61),
    "TSH_mIU_L": (0.4, 4.0),
    "T4_livre_ng_dL": (0.8, 1.8),
    "troponina_T_ng_mL": (0, 0.014),
}


def analisar_tendencias(exames: list[dict[str, Any]]) -> dict[str, Any]:
    if not exames:
        return {}

    df = pd.DataFrame(exames).sort_values("data_coleta")
    valores = df["valor"].to_numpy(dtype=float)
    datas = pd.to_datetime(df["data_coleta"])
    dias = (datas - datas.min()).dt.days.to_numpy()

    estatisticas: dict[str, Any] = {
        "min": float(np.min(valores)),
        "max": float(np.max(valores)),
        "media": float(np.mean(valores)),
        "desvio_padrao": float(np.std(valores)),
        "ultimo_valor": float(valores[-1]),
        "primeiro_valor": float(valores[0]),
        "delta": float(valores[-1] - valores[0]),
        "delta_percentual": float((valores[-1] - valores[0]) / valores[0] * 100) if valores[0] != 0 else 0.0,
        "num_medicoes": int(len(valores)),
        "significativa": False,
    }

    if len(valores) >= 3:
        slope, _, r_value, p_value, _ = stats.linregress(dias, valores)
        estatisticas["tendencia_slope"] = float(slope)
        estatisticas["tendencia_r2"] = float(r_value**2)
        estatisticas["tendencia_p"] = float(p_value)
        estatisticas["significativa"] = bool(p_value < 0.05)
        estatisticas["tendencia_direcao"] = "crescente" if slope > 0 else "decrescente"

    return estatisticas


def detectar_mudancas_significativas(exames_por_tipo: dict[str, list[dict]]) -> dict[str, Any]:
    return {
        tipo: analisar_tendencias(lista)
        for tipo, lista in exames_por_tipo.items()
        if len(lista) >= 2
    }


def verificar_valores_referencia(valor: float, nome_exame: str) -> dict[str, Any]:
    if nome_exame in REFERENCIAS:
        ref_min, ref_max = REFERENCIAS[nome_exame]
        if valor < ref_min:
            return {"status": "baixo", "mensagem": f"Valor abaixo do normal ({ref_min}-{ref_max})"}
        if valor > ref_max:
            return {"status": "alto", "mensagem": f"Valor acima do normal ({ref_min}-{ref_max})"}
    return {"status": "normal", "mensagem": ""}

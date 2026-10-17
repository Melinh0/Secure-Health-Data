import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import init_db, session_scope
from app.models import AnotacaoClinica, Exame, Paciente
from app.services.anonimizacao import gerar_nome_anon
from app.services.exames import para_valor_exame

CAMPOS_EXAME = [
    "hemoglobina_g_dL", "eritrocitos_milhoes_uL", "leucocitos_mm3", "plaquetas_mm3",
    "colesterol_total_mg_dL", "triglicerides_mg_dL", "glicose_mg_dL", "creatinina_mg_dL",
    "vitamina_B12_pg_mL", "vitamina_D_ng_mL", "TGO_AST_U_L", "TGP_ALT_U_L", "GGT_U_L",
    "TSH_mIU_L", "T4_livre_ng_dL", "troponina_T_ng_mL",
]

ANOTACOES = [
    "Paciente queixa-se de humor deprimido, insônia e fadiga.",
    "Paciente relata melhora do humor, mas persistência de ansiedade.",
    "Paciente refere uso regular de medicação, sem efeitos colaterais relatados.",
    "Paciente relata ganho de peso e apetite aumentado nas últimas semanas.",
]


def _parse_data(valor):
    if valor is None or pd.isna(valor):
        return None
    try:
        return pd.to_datetime(valor, dayfirst=True).to_pydatetime()
    except Exception:
        return None


def seed(dados_csv: str = "data/synthetic_patient_data_1000.csv") -> None:
    init_db()

    with session_scope() as db:
        if db.query(Paciente).count() > 0:
            print("Banco já populado — seed ignorado.")
            return

        df = pd.read_csv(dados_csv)
        grupos: dict[str, list[dict]] = {}
        for _, row in df.iterrows():
            grupos.setdefault(row["nome_completo"], []).append(row.to_dict())

        for nome_original, linhas in grupos.items():
            paciente = Paciente(
                nome_anon=gerar_nome_anon(nome_original),
                data_nascimento=_parse_data(linhas[0].get("data_nascimento")),
                sexo=linhas[0].get("sexo"),
            )
            db.add(paciente)
            db.flush()

            num_medicoes = random.randint(5, 12)
            datas = sorted(datetime.now() - timedelta(days=random.randint(0, 365)) for _ in range(num_medicoes))

            for i, data_coleta in enumerate(datas):
                linha = dict(random.choice(linhas))
                for col in CAMPOS_EXAME:
                    val = para_valor_exame(linha.get(col))
                    if val is not None:
                        linha[col] = val * (1 + random.uniform(-0.1, 0.1))

                for col in CAMPOS_EXAME:
                    val = para_valor_exame(linha.get(col))
                    if val is not None:
                        db.add(Exame(
                            paciente_id=paciente.id,
                            data_coleta=data_coleta,
                            exame_nome=col,
                            valor=float(val),
                            unidade="",
                        ))

                texto = f"Consulta {i + 1}. {random.choice(ANOTACOES)} "
                texto += f"ECG: {linha.get('eletrocardiograma_ECG', 'normal')}."
                db.add(AnotacaoClinica(
                    paciente_id=paciente.id,
                    data=data_coleta,
                    texto=texto,
                    tipo="evolucao",
                ))

        total_pacientes = db.query(Paciente).count()
        total_exames = db.query(Exame).count()
        print(f"Seed concluído: {total_pacientes} pacientes, {total_exames} exames.")


if __name__ == "__main__":
    seed()

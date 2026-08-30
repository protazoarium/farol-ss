"""Detector 2 — resíduo do ajuste necessidade→alocação, escala robusta."""

import numpy as np
import pandas as pd

from farol_ss.index.anomalies import detectar_residuo_alocacao


def _grade(n=40, semente=0):
    rng = np.random.default_rng(semente)
    nec = np.sort(rng.uniform(0, 1, n))
    # alocação segue a necessidade (ruído pequeno) — relação forte do "estado"
    aloc = np.clip(0.15 + 0.7 * nec + rng.normal(0, 0.03, n), 0, 1)
    return pd.DataFrame(
        {
            "cod_ibge": [f"26{i:05d}" for i in range(n)],
            "ano": 2024,
            "necessidade_rank": nec,
            "alocacao_rank": aloc,
            "alocacao_cobertura": 1.0,
        }
    )


def test_municipio_muito_abaixo_da_reta_dispara():
    df = _grade()
    # um município de alta necessidade recebe alocação de piso
    df.loc[df.index[-1], "alocacao_rank"] = 0.05
    alertas = detectar_residuo_alocacao(df)
    assert (alertas["cod_ibge"] == df.loc[df.index[-1], "cod_ibge"]).any()
    assert alertas["tipo"].eq("alocacao_abaixo_do_esperado").all()
    assert (alertas["residuo_z"] < 0).all()


def test_grade_bem_comportada_nao_dispara():
    assert detectar_residuo_alocacao(_grade(semente=3)).empty


def test_so_considera_eixo_alocacao_completo():
    df = _grade()
    df["alocacao_cobertura"] = 0.667  # incompleto
    df.loc[df.index[-1], "alocacao_rank"] = 0.05
    assert detectar_residuo_alocacao(df).empty


def test_amostra_pequena_e_ignorada():
    df = _grade(n=10)
    df.loc[df.index[-1], "alocacao_rank"] = 0.02
    assert detectar_residuo_alocacao(df).empty


def test_schema_vazio_sem_colunas():
    out = detectar_residuo_alocacao(pd.DataFrame({"cod_ibge": ["x"], "ano": [2024]}))
    assert out.empty
    assert list(out.columns) == [
        "cod_ibge",
        "ano",
        "tipo",
        "severidade",
        "residuo_z",
        "explicacao",
    ]

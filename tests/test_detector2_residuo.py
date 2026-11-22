"""Detector 2 — resíduo do ajuste log(R$ per capita) ~ necessidade, escala robusta."""

import numpy as np
import pandas as pd

from farol_ss.index.anomalies import detectar_residuo_alocacao


def _grade(n=40, semente=0):
    rng = np.random.default_rng(semente)
    nec = np.sort(rng.uniform(0, 1, n))
    # R$ per capita cresce com a necessidade (log-linear, ruído pequeno)
    aloc = np.exp(6.0 + 0.8 * nec + rng.normal(0, 0.03, n))
    return pd.DataFrame(
        {
            "cod_ibge": [f"26{i:05d}" for i in range(n)],
            "ano": 2024,
            "necessidade_rank": nec,
            "alocacao_bruta": aloc,
            "alocacao_cobertura": 1.0,
        }
    )


def test_municipio_muito_abaixo_da_reta_dispara():
    df = _grade()
    # um município de alta necessidade recebe 40% do que a relação do estado prevê
    df.loc[df.index[-1], "alocacao_bruta"] *= 0.4
    alertas = detectar_residuo_alocacao(df)
    assert (alertas["cod_ibge"] == df.loc[df.index[-1], "cod_ibge"]).any()
    assert alertas["tipo"].eq("alocacao_abaixo_do_esperado").all()
    assert (alertas["residuo_z"] < 0).all()
    assert "abaixo" in alertas["explicacao"].iloc[0]


def test_grade_bem_comportada_nao_dispara():
    assert detectar_residuo_alocacao(_grade(semente=3)).empty


def test_queda_pequena_nao_dispara_mesmo_com_z_alto():
    # ruído quase nulo: z enorme para um desvio de 10%, mas abaixo do piso prático de 20%
    df = _grade()
    ruido = np.random.default_rng(1).normal(0, 0.003, len(df))
    df["alocacao_bruta"] = np.exp(6.0 + 0.8 * df["necessidade_rank"] + ruido)
    df.loc[df.index[-1], "alocacao_bruta"] *= 0.9
    assert detectar_residuo_alocacao(df).empty


def test_so_considera_eixo_alocacao_completo():
    df = _grade()
    df["alocacao_cobertura"] = 0.5  # incompleto
    df.loc[df.index[-1], "alocacao_bruta"] *= 0.4
    assert detectar_residuo_alocacao(df).empty


def test_amostra_pequena_e_ignorada():
    df = _grade(n=10)
    df.loc[df.index[-1], "alocacao_bruta"] *= 0.3
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

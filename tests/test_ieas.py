"""Testes do IEAS com fixtures sintéticas — não dependem do pipeline real.

Conforme o plano: "município de necessidade alta e alocação baixa precisa
dar vermelho; alta/alta dá verde; cobertura abaixo do limiar dá cinza e
nunca um número".
"""

import numpy as np
import pandas as pd

from farol_ss.index.ieas import calcular_ieas, classificar_farol


def _municipios(n=20, seed=0):
    """N municípios sintéticos com sub-índices já normalizados em [0,1]."""
    rng = np.random.default_rng(seed)
    return pd.DataFrame(
        {
            "cod_ibge": [f"26{i:05d}" for i in range(n)],
            "sub_epidemiologico": rng.uniform(0, 1, n),
            "sub_saneamento": rng.uniform(0, 1, n),
            "sub_vulnerabilidade": rng.uniform(0, 1, n),
            "l1_per_capita": rng.uniform(0, 1, n),
            "l2_per_capita": rng.uniform(0, 1, n),
            "l3_per_capita": rng.uniform(0, 1, n),
        }
    )


def test_alta_necessidade_baixa_alocacao_da_vermelho():
    df = _municipios(n=20)
    # Município 0: necessidade máxima, alocação mínima -> gap muito negativo
    df.loc[0, ["sub_epidemiologico", "sub_saneamento", "sub_vulnerabilidade"]] = 1.0
    df.loc[0, ["l1_per_capita", "l2_per_capita", "l3_per_capita"]] = 0.0

    out = calcular_ieas(df)
    assert out.loc[0, "farol"] == "vermelho"
    assert out.loc[0, "gap"] < 0


def test_alta_necessidade_alta_alocacao_da_verde():
    df = _municipios(n=20)
    df.loc[0, ["sub_epidemiologico", "sub_saneamento", "sub_vulnerabilidade"]] = 1.0
    df.loc[0, ["l1_per_capita", "l2_per_capita", "l3_per_capita"]] = 1.0

    out = calcular_ieas(df)
    assert out.loc[0, "farol"] == "verde"
    assert abs(out.loc[0, "gap"]) <= 0.10


def test_baixa_necessidade_alta_alocacao_da_azul():
    df = _municipios(n=20)
    df.loc[0, ["sub_epidemiologico", "sub_saneamento", "sub_vulnerabilidade"]] = 0.0
    df.loc[0, ["l1_per_capita", "l2_per_capita", "l3_per_capita"]] = 1.0

    out = calcular_ieas(df)
    assert out.loc[0, "farol"] == "azul"
    assert out.loc[0, "gap"] > 0


def test_cobertura_insuficiente_da_cinza_nunca_numero():
    """Município com só 1 dos 3 subíndices de necessidade presentes
    (cobertura 33% < mínimo 60%) não pode ter IEAS calculado."""
    df = _municipios(n=20)
    df.loc[0, "sub_saneamento"] = np.nan
    df.loc[0, "sub_vulnerabilidade"] = np.nan
    # sub_epidemiologico continua presente -> cobertura = 1/3 = 0.33 < 0.60

    out = calcular_ieas(df)
    assert out.loc[0, "farol"] == "cinza"
    assert pd.isna(out.loc[0, "ieas"])
    assert pd.isna(out.loc[0, "gap"])


def test_cobertura_suficiente_apesar_de_um_componente_faltante():
    """2 de 3 componentes de necessidade presentes = 67% >= 60%: calcula
    normalmente (renormalizando os pesos), não vira cinza."""
    df = _municipios(n=20)
    df.loc[0, "sub_vulnerabilidade"] = np.nan

    out = calcular_ieas(df)
    assert out.loc[0, "farol"] != "cinza"
    assert pd.notna(out.loc[0, "ieas"])


def test_classificar_farol_limiares_exatos():
    conf_gaps = pd.Series([-0.5, -0.33, -0.20, -0.10, 0.0, 0.10, 0.20, 0.33, 0.5, np.nan])
    cores = classificar_farol(conf_gaps)
    assert list(cores) == [
        "vermelho",  # -0.50
        "vermelho",  # -0.33 (limiar inclusivo)
        "amarelo",  # -0.20
        "amarelo",  # -0.10 (limiar inclusivo)
        "verde",  # 0.00
        "verde",  # 0.10 (limiar inclusivo)
        "verde",  # 0.20 (zona entre verde_ate e azul_a_partir)
        "azul",  # 0.33 (limiar inclusivo)
        "azul",  # 0.50
        "cinza",  # NaN
    ]


def test_ieas_e_gap_tem_relacao_esperada():
    """ieas = 1 - |gap|, sempre em [0, 1] onde definido."""
    df = _municipios(n=30)
    out = calcular_ieas(df)
    validos = out.dropna(subset=["ieas", "gap"])
    assert (validos["ieas"] == (1 - validos["gap"].abs())).all()
    assert (validos["ieas"] >= 0).all() and (validos["ieas"] <= 1).all()

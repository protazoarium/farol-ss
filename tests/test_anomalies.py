"""Testes dos detectores 1 e 4 com fixtures sintéticas.

Do plano: "fixture com surto e zero compra dispara o detector 4".
"""

import numpy as np
import pandas as pd

from farol_ss.index.anomalies import (
    detectar_desabastecimento,
    detectar_desalinhamento_estrutural,
)
from farol_ss.index.ieas import calcular_ieas


def test_detector1_so_sinaliza_farol_vermelho():
    rng = np.random.default_rng(1)
    n = 15
    df = pd.DataFrame(
        {
            "cod_ibge": [f"26{i:05d}" for i in range(n)],
            "ano": 2024,
            "sub_epidemiologico": rng.uniform(0, 1, n),
            "sub_saneamento": rng.uniform(0, 1, n),
            "sub_vulnerabilidade": rng.uniform(0, 1, n),
            "l1_per_capita": rng.uniform(0, 1, n),
            "l2_per_capita": rng.uniform(0, 1, n),
            "l3_per_capita": rng.uniform(0, 1, n),
        }
    )
    df.loc[0, ["sub_epidemiologico", "sub_saneamento", "sub_vulnerabilidade"]] = 1.0
    df.loc[0, ["l1_per_capita", "l2_per_capita", "l3_per_capita"]] = 0.0

    out = calcular_ieas(df)
    alertas = detectar_desalinhamento_estrutural(out)

    assert (alertas["cod_ibge"] == df.loc[0, "cod_ibge"]).any()
    assert alertas["explicacao"].str.len().gt(0).all()


def test_detector4_surto_sem_compra_dispara_alerta():
    """Município com incidência de dengue no topo da distribuição e ZERO
    compra de larvicida/inseticida deve aparecer no alerta."""
    epidemiologia = pd.DataFrame(
        {
            "cod_ibge": ["2600054", "2600104", "2600203", "2600302"],
            "ano": [2024, 2024, 2024, 2024],
            "taxa_deng": [500.0, 10.0, 12.0, 8.0],  # município 0 em surto
        }
    )
    # PNCP: ninguém comprou nada relacionado a dengue
    compras = pd.DataFrame(
        {
            "cod_ibge": ["2600104"],
            "ano": [2024],
            "objeto_compra": ["Contratação de serviço de limpeza urbana"],
        }
    )

    alertas = detectar_desabastecimento(epidemiologia, compras)
    assert (alertas["cod_ibge"] == "2600054").any()
    assert "dengue" in alertas.iloc[0]["explicacao"].lower() or "Dengue" in alertas.iloc[0]["agravo"]


def test_detector4_nao_dispara_quando_municipio_comprou_insumo():
    epidemiologia = pd.DataFrame(
        {"cod_ibge": ["2600054"], "ano": [2024], "taxa_deng": [500.0]}
    )
    compras = pd.DataFrame(
        {
            "cod_ibge": ["2600054"],
            "ano": [2024],
            "objeto_compra": ["Aquisição de larvicida biológico para combate ao Aedes aegypti"],
        }
    )
    alertas = detectar_desabastecimento(epidemiologia, compras)
    assert alertas.empty


def test_detector4_sem_dado_de_compras_devolve_tabela_vazia_com_schema():
    epidemiologia = pd.DataFrame({"cod_ibge": ["2600054"], "ano": [2024], "taxa_deng": [500.0]})
    alertas = detectar_desabastecimento(epidemiologia, None)
    assert alertas.empty
    assert list(alertas.columns) == ["cod_ibge", "ano", "tipo", "severidade", "agravo", "explicacao"]

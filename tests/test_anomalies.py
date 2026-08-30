"""Testes dos detectores 1, 3 e 4 com fixtures sintéticas.

Do plano: "fixture com surto e zero compra dispara o detector 4".
"""

import numpy as np
import pandas as pd

from farol_ss.index.anomalies import (
    detectar_desabastecimento,
    detectar_desalinhamento_estrutural,
    detectar_sobrepreco,
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
    """Município com incidência de dengue no topo da distribuição que
    contratou no PNCP no período, mas nada de larvicida/inseticida, deve
    aparecer no alerta. (O detector só olha município-ano que APARECE no
    PNCP — sem nenhuma compra publicada é lacuna de dado, não de política.)"""
    epidemiologia = pd.DataFrame(
        {
            "cod_ibge": ["2600054", "2600104", "2600203", "2600302"],
            "ano": [2024, 2024, 2024, 2024],
            "taxa_deng": [500.0, 10.0, 12.0, 8.0],  # município 0 em surto
        }
    )
    # PNCP: o município em surto contratou, mas nada relacionado a dengue
    compras = pd.DataFrame(
        {
            "cod_ibge": ["2600054", "2600104"],
            "ano": [2024, 2024],
            "objeto_compra": [
                "Contratação de empresa para pavimentação asfáltica de vias",
                "Contratação de serviço de limpeza urbana",
            ],
        }
    )

    alertas = detectar_desabastecimento(epidemiologia, compras)
    assert (alertas["cod_ibge"] == "2600054").any()
    assert (
        "dengue" in alertas.iloc[0]["explicacao"].lower() or "Dengue" in alertas.iloc[0]["agravo"]
    )


def test_detector4_surto_sem_nenhuma_compra_no_pncp_nao_dispara():
    """Município em surto que não aparece no PNCP naquele ano não vira alerta:
    é ausência de dado (cobertura do portal), não ausência de resposta."""
    epidemiologia = pd.DataFrame({"cod_ibge": ["2600054"], "ano": [2024], "taxa_deng": [500.0]})
    compras = pd.DataFrame(
        {"cod_ibge": ["2600104"], "ano": [2024], "objeto_compra": ["Limpeza urbana"]}
    )
    alertas = detectar_desabastecimento(epidemiologia, compras)
    assert alertas.empty


def test_detector4_nao_dispara_quando_municipio_comprou_insumo():
    epidemiologia = pd.DataFrame({"cod_ibge": ["2600054"], "ano": [2024], "taxa_deng": [500.0]})
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
    assert list(alertas.columns) == [
        "cod_ibge",
        "ano",
        "tipo",
        "severidade",
        "agravo",
        "explicacao",
    ]


def _itens_sinteticos(precos_por_municipio: dict[str, float]) -> pd.DataFrame:
    """Um item de 'praziquantel comprimido' por município, ao preço dado."""
    return pd.DataFrame(
        {
            "cod_ibge": list(precos_por_municipio),
            "ano": 2024,
            "numero_controle_pncp": [
                f"00000000000000-1-{i:06d}/2024" for i in range(len(precos_por_municipio))
            ],
            "numero_item": 1,
            "descricao": "Praziquantel comprimido 600mg",
            "material_ou_servico": "Material",
            "quantidade": 100.0,
            "unidade_medida": "COMPRIMIDO",
            "valor_unitario_estimado": list(precos_por_municipio.values()),
            "valor_total": [p * 100 for p in precos_por_municipio.values()],
            "item_categoria_nome": "Medicamentos",
            "orcamento_sigiloso": False,
        }
    )


def test_detector3_preco_muito_acima_do_iqr_dispara():
    # 8 municípios pagam ~R$ 1,00; um paga R$ 20,00
    precos = {f"26000{i:02d}": 1.0 + 0.1 * i for i in range(8)}
    precos["2699999"] = 20.0
    alertas = detectar_sobrepreco(_itens_sinteticos(precos))
    assert (alertas["cod_ibge"] == "2699999").any()
    assert alertas["tipo"].eq("suspeita_sobrepreco").all()
    assert "praziquantel" in alertas.iloc[0]["categoria"]


def test_detector3_precos_homogeneos_nao_disparam():
    precos = {f"26000{i:02d}": 1.0 + 0.02 * i for i in range(10)}
    assert detectar_sobrepreco(_itens_sinteticos(precos)).empty


def test_detector3_sem_itens_devolve_schema_vazio():
    out = detectar_sobrepreco(None)
    assert out.empty
    assert list(out.columns) == ["cod_ibge", "ano", "tipo", "severidade", "categoria", "explicacao"]


def test_detector3_ignora_servico_e_orcamento_sigiloso():
    df = _itens_sinteticos({f"26000{i:02d}": 1.0 for i in range(6)})
    df.loc[len(df)] = df.iloc[0].to_dict()
    df.loc[len(df) - 1, ["cod_ibge", "valor_unitario_estimado", "material_ou_servico"]] = (
        "2688888",
        99.0,
        "Serviço",
    )
    df.loc[len(df)] = df.iloc[0].to_dict()
    df.loc[len(df) - 1, ["cod_ibge", "valor_unitario_estimado", "orcamento_sigiloso"]] = (
        "2677777",
        99.0,
        True,
    )
    alertas = detectar_sobrepreco(df)
    assert not alertas["cod_ibge"].isin(["2688888", "2677777"]).any()

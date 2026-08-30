"""Garantias de grão da camada gold — se isto quebra, todo o resto é suspeito.

O plano exige: nenhuma linha do gold com cod_ibge órfão; nenhum par
(cod_ibge, ano) duplicado; grade completa 185 × anos do recorte.
"""

import pytest

from farol_ss import config
from farol_ss.io import municipios as M
from farol_ss.transform.gold_municipio_ano import _deflator_por_ano, montar


@pytest.fixture(scope="module")
def gold():
    if not (config.SILVER / "ibge_populacao.parquet").exists():
        pytest.skip("requer `make ingest` executado (dados reais em data/silver)")
    return montar()


def test_grao_completo_sem_duplicatas(gold):
    assert len(gold) == 185 * len(config.anos())
    assert not gold.duplicated(subset=["cod_ibge", "ano"]).any()


def test_sem_codigo_orfao(gold):
    assert gold["cod_ibge"].isin(M.codigos()).all()


def test_todos_os_municipios_presentes(gold):
    assert set(gold["cod_ibge"]) == M.codigos()


def test_taxas_nao_negativas(gold):
    taxas = [c for c in gold.columns if c.startswith("taxa_")]
    for c in taxas:
        assert (gold[c] >= 0).all(), f"{c} tem valor negativo"


def test_populacao_positiva_onde_presente(gold):
    com_pop = gold["populacao"].dropna()
    assert (com_pop > 0).all()


def test_l3_per_capita_nao_negativo_e_esparso(gold):
    """L3 vem do PNCP, que não cobre todo município-ano — a coluna é esparsa
    de propósito. Onde existe, é ≥ 0."""
    assert "l3_per_capita" in gold.columns
    presente = gold["l3_per_capita"].dropna()
    assert (presente >= 0).all()
    assert 0 < len(presente) < len(gold)  # nem vazia, nem completa


def test_deflator_leva_ano_base_para_um(gold):
    """O fator do ano-base de deflação deve ser 1.0 (referência de si mesmo)."""
    base = config.recorte()["ano_base_deflacao"]
    deflator = _deflator_por_ano()
    assert deflator[base] == pytest.approx(1.0)
    # anos anteriores ao base inflacionam: fator > 1
    assert all(deflator[a] >= 1.0 for a in deflator if a < base)

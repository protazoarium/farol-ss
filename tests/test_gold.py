"""Garantias de grão da camada gold — se isto quebra, todo o resto é suspeito.

O plano exige: nenhuma linha do gold com cod_ibge órfão; nenhum par
(cod_ibge, ano) duplicado; grade completa 185 × anos do recorte.
"""

import pytest

from farol_ss import config
from farol_ss.io import municipios as M
from farol_ss.transform.gold_municipio_ano import montar


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

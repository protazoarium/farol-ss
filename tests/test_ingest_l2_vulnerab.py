"""Testes dos parsers de SIOPS (L2) e CadÚnico (vulnerabilidade).

Sem rede: exercitam só a extração/normalização a partir de payloads fixos
representativos do que o TabNet do SIOPS e o Solr do SAGI devolvem.
"""

import pandas as pd

from farol_ss.ingest.cadunico import _int
from farol_ss.ingest.siops import _num_br

_SIOPS_HTML = """
<TABLE BORDER>
<TR ALIGN=RIGHT>
<TH ALIGN=LEFT>Munic&iacute;pios<TH>D.R.Pr&oacute;prios em Sa&uacute;de/Hab
<TR ALIGN=RIGHT>
<TH ALIGN=LEFT> TOTAL
<TD>513,23
<TR ALIGN=RIGHT>
<TH ALIGN=LEFT>260005 Abreu e Lima
<TD>254,81
<TR ALIGN=RIGHT>
<TH ALIGN=LEFT>260130 Barra de Guabiraba
<TD>1.000,88
</TABLE>
"""


def test_num_br_converte_decimal_brasileiro():
    assert _num_br("254,81") == 254.81
    assert _num_br("1.000,88") == 1000.88
    assert _num_br("-") is None
    assert _num_br("") is None


def test_int_cadunico_aceita_string_e_none():
    assert _int("2890") == 2890.0
    assert _int(161) == 161.0
    assert _int(None) is None
    assert _int("n/d") is None


def test_siops_regex_extrai_municipios_e_valores():
    import re

    pares = re.findall(r"<TH ALIGN=LEFT>\s*(\d{6})\s[^<]*<TD>([^<]+)", _SIOPS_HTML, re.IGNORECASE)
    codigos = {c for c, _ in pares}
    assert codigos == {"260005", "260130"}  # "TOTAL" (sem código) fica de fora
    valores = {c: _num_br(v) for c, v in pares}
    assert valores["260130"] == 1000.88


def test_gold_junta_l2_e_vulnerabilidade_quando_silver_existe():
    """Se os silver de SIOPS e CadÚnico existem, o gold ganha as colunas do
    eixo Alocação L2 e do subíndice de vulnerabilidade."""
    from farol_ss import config
    from farol_ss.transform.gold_municipio_ano import montar

    if not (config.SILVER / "ibge_populacao.parquet").exists():
        import pytest

        pytest.skip("requer data/silver (make ingest)")

    gold = montar()
    if (config.SILVER / "siops.parquet").exists():
        assert "l2_per_capita" in gold.columns
        assert (gold["l2_per_capita"].dropna() >= 0).all()
    if (config.SILVER / "cadunico.parquet").exists():
        assert "extrema_pobreza_por_mil_hab" in gold.columns
        assert (gold["extrema_pobreza_por_mil_hab"].dropna() > 0).all()
        assert pd.api.types.is_float_dtype(gold["extrema_pobreza_por_mil_hab"])

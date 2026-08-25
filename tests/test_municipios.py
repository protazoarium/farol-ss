"""Integridade da dimensão municipal — se isto quebra, todo o resto mente."""

import pandas as pd

from farol_ss.io import municipios as M


def test_sao_185_municipios():
    assert len(M.municipios()) == 185


def test_codigos_ibge_validos():
    cods = M.municipios()["cod_ibge"]
    assert cods.str.match(r"^26\d{5}$").all(), "todo município de PE começa em 26"
    assert cods.is_unique


# Quixaba/PE (2611533) não satisfaz o dígito verificador, e o código vem da
# própria API do IBGE — é exceção real da base, não erro de digitação nossa.
# Por isso o teste tolera esta única divergência em vez de exigir 100%, o que
# codificaria um invariante falso. Continua valendo para os outros 184.
DV_EXCECOES = {"2611533"}


def test_digito_verificador_ibge():
    """O 7º dígito do código IBGE é verificador (pesos 1,2 alternados, módulo 10)."""

    def dv(cod6: str) -> str:
        pesos = [1, 2, 1, 2, 1, 2]
        total = 0
        for d, p in zip(cod6, pesos):
            prod = int(d) * p
            total += prod if prod < 10 else (prod // 10) + (prod % 10)
        return str((10 - total % 10) % 10)

    ruins = {c for c in M.municipios()["cod_ibge"] if c[6] != dv(c[:6])}
    assert ruins == DV_EXCECOES, f"dígito verificador inesperado em {ruins - DV_EXCECOES}"


def test_sem_artefato_de_encoding():
    txt = M.municipios().to_csv()
    assert "¿" not in txt, "artefato U+00BF da API do IBGE vazou para o seed"


def test_municipios_conhecidos_presentes():
    nomes = set(M.municipios()["nome"])
    for esperado in ["Recife", "Caruaru", "Petrolina", "Fernando de Noronha"]:
        assert esperado in nomes


def test_resolve_codigo_de_6_digitos():
    # DATASUS publica Recife como 261160 (6 dígitos); o padrão do projeto é 2611606
    assert M.resolve_por_codigo(pd.Series(["261160"])).iloc[0] == "2611606"
    # e 260160 é outro município de verdade, não o Recife truncado
    assert M.resolve_por_codigo(pd.Series(["260160"])).iloc[0] == "2601607"


def test_resolve_codigo_rejeita_fora_de_pe():
    # 3550308 = São Paulo; não pertence ao recorte
    assert pd.isna(M.resolve_por_codigo(pd.Series(["3550308"])).iloc[0])


def test_resolve_por_nome_tolera_acento_e_caixa():
    assert M.resolve_por_nome(pd.Series(["SAO LOURENCO DA MATA"])).iloc[0] == "2613701"


def test_cobertura():
    assert M.cobertura(M.municipios()) == 1.0

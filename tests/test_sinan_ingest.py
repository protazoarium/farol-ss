"""Regressão dos dois bugs corrigidos em `_filtrar_pe` (ver docstring do
módulo `farol_ss.ingest.sinan`):

1. `ID_MN_RESI` no Parquet cru do DATASUS é o código de 6 dígitos sem dígito
   verificador — um `lpad` ingênuo produzia um código que não batia com
   nenhum município e descartava tudo silenciosamente.
2. O grão correto é contagem de notificações por (cod_ibge, ano), não linhas
   deduplicadas — `.drop_duplicates()` colapsava vários casos do mesmo dia
   com a mesma classificação, subcontando incidência num surto.

O teste grava um Parquet sintético no formato bruto do DATASUS (6 dígitos,
sem DV) e verifica que a contagem final bate com o número de notificações,
não com o número de combinações únicas de (código, data, classificação).
"""

import pandas as pd
import pytest

from farol_ss.ingest.sinan import _filtrar_pe

# Recife = 2611606 (7 dígitos) -> 261160 no formato bruto do DATASUS (6, sem DV)
RECIFE_BRUTO = "261160"
# Bodocó = 2602001 -> 260200 bruto; é o caso que reconstrução ingênua corrompia
BODOCO_BRUTO = "260200"


@pytest.fixture
def parquet_sinan_sintetico(tmp_path):
    """3 notificações em Recife no mesmo dia com a mesma classificação (um
    dedup ingênuo colapsaria em 1) + 1 em Bodocó, formato bruto DATASUS."""
    df = pd.DataFrame(
        {
            "ID_MN_RESI": [RECIFE_BRUTO, RECIFE_BRUTO, RECIFE_BRUTO, BODOCO_BRUTO],
            "DT_NOTIFIC": ["2024-03-01", "2024-03-01", "2024-03-01", "2024-05-10"],
            "CLASSI_FIN": ["10", "10", "10", "5"],
        }
    )
    path = tmp_path / "DENGBR24.parquet"
    df.to_parquet(path)
    return str(path)


def test_nao_deduplica_notificacoes_do_mesmo_dia(parquet_sinan_sintetico):
    """As 3 notificações de Recife devem contar como 3 casos, não 1."""
    out = _filtrar_pe(parquet_sinan_sintetico, ano=2024)
    recife = out[out.cod_ibge == "2611606"]
    assert recife["casos"].iloc[0] == 3


def test_reconstroi_codigo_de_6_digitos_corretamente(parquet_sinan_sintetico):
    """Bodocó não pode ser confundido com outro município pela reconstrução."""
    out = _filtrar_pe(parquet_sinan_sintetico, ano=2024)
    assert "2602001" in set(out.cod_ibge)
    bodoco = out[out.cod_ibge == "2602001"]
    assert bodoco["casos"].iloc[0] == 1


def test_codigo_fora_de_pe_e_descartado(tmp_path):
    df = pd.DataFrame(
        {
            "ID_MN_RESI": ["355030"],  # São Paulo, fora do recorte
            "DT_NOTIFIC": ["2024-01-01"],
            "CLASSI_FIN": ["10"],
        }
    )
    path = tmp_path / "DENGBR24_sp.parquet"
    df.to_parquet(path)
    assert _filtrar_pe(str(path), ano=2024) is None


def test_ano_vem_da_data_de_notificacao_nao_do_nome_do_arquivo(tmp_path):
    """Notificação de dez/2023 num arquivo nomeado 2024 deve contar em 2023."""
    df = pd.DataFrame(
        {
            "ID_MN_RESI": [RECIFE_BRUTO],
            "DT_NOTIFIC": ["2023-12-30"],
            "CLASSI_FIN": ["10"],
        }
    )
    path = tmp_path / "DENGBR24_virada.parquet"
    df.to_parquet(path)
    out = _filtrar_pe(str(path), ano=2024)
    assert out["ano"].iloc[0] == 2023

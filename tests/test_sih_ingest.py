"""Testes da ingestão do SIH (grupo RD) e do casamento de CID DRSAI."""

import pandas as pd

from farol_ss.ingest import sih


def test_cids_drsai_sao_do_grupo_veiculacao_hidrica():
    cids = sih._cids_drsai()
    # do seeds/cid_saneamento.csv, grupo veiculacao_hidrica
    assert "A09" in cids  # diarreia
    assert "B15" in cids  # hepatite A
    assert "A27" in cids  # leptospirose
    # arboviroses NÃO entram no subíndice de internações por saneamento
    assert "A90" not in cids


def test_e_drsai_casa_por_codigo_cheio_e_por_prefixo():
    cids = sih._cids_drsai()
    diag = pd.Series(["A090", "A09", "B159", "S930", "A900", "I10"])
    marca = sih._e_drsai(diag, cids)
    # A090 -> prefixo A09 (diarreia); B159 -> prefixo B15 (hepatite A)
    assert marca.tolist() == [True, True, True, False, False, False]


def test_filtrar_pe_agrega_por_municipio_de_residencia(tmp_path):
    """DIAG_PRINC de saneamento contam em internacoes_drsai; o resto só no total.
    MUNIC_RES fora de PE é descartado."""
    bruto = pd.DataFrame(
        {
            "MUNIC_RES": ["261160", "261160", "261160", "355030"],  # 3 Recife + 1 SP
            "DIAG_PRINC": ["A090", "B15", "I10", "A09"],
        }
    )
    p = tmp_path / "RDPE2301.parquet"
    bruto.to_parquet(p)

    out = sih._filtrar_pe([str(p)], 2023, sih._cids_drsai())
    assert len(out) == 1
    linha = out.iloc[0]
    assert linha["cod_ibge"] == "2611606"
    assert linha["ano"] == 2023
    assert linha["internacoes_total"] == 3
    assert linha["internacoes_drsai"] == 2  # A090 + B15

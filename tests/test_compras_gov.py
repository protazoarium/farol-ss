"""Testes do L3 federal (Compras.gov.br) — filtro de esfera e de saúde."""

from farol_ss.ingest.compras_gov import _e_saude, _linha_federal_de_saude

_PE = {"2611606"}  # Recife


def test_descarta_esfera_municipal():
    """A esfera municipal aqui é a mesma que o PNCP já traz — descartar."""
    c = {
        "orgaoEntidadeEsferaId": "M",
        "unidadeOrgaoCodigoIbge": 2611606,
        "objetoCompra": "Aquisição de medicamentos",
        "numeroControlePNCP": "x",
    }
    assert _linha_federal_de_saude(c, 2024, "Dispensa", _PE) is None


def test_descarta_federal_fora_de_pe():
    c = {
        "orgaoEntidadeEsferaId": "F",
        "unidadeOrgaoCodigoIbge": 3550308,  # São Paulo
        "objetoCompra": "Aquisição de medicamentos",
        "numeroControlePNCP": "x",
    }
    assert _linha_federal_de_saude(c, 2024, "Dispensa", _PE) is None


def test_descarta_federal_em_pe_que_nao_e_saude():
    c = {
        "orgaoEntidadeEsferaId": "F",
        "unidadeOrgaoCodigoIbge": 2611606,
        "objetoCompra": "Locação de veículos para a superintendência",
        "numeroControlePNCP": "x",
    }
    assert _linha_federal_de_saude(c, 2024, "Dispensa", _PE) is None


def test_aceita_federal_de_saude_em_pe():
    c = {
        "orgaoEntidadeEsferaId": "F",
        "unidadeOrgaoCodigoIbge": 2611606,
        "objetoCompra": "Aquisição de material médico-hospitalar",
        "numeroControlePNCP": "10979565000116-1-000001/2024",
        "valorTotalHomologado": 1980.0,
    }
    linha = _linha_federal_de_saude(c, 2024, "Dispensa", _PE)
    assert linha is not None
    assert linha["cod_ibge"] == "2611606"
    assert linha["ano"] == 2024
    assert linha["valor_total_homologado"] == 1980.0


def test_e_saude_reconhece_termos_de_insumo():
    assert _e_saude("AQUISIÇÃO DE MEDICAMENTOS E CORRELATOS")
    assert _e_saude("material médico-hospitalar")
    assert not _e_saude("reforma de telhado do galpão")

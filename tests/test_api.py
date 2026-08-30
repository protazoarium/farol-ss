"""Fumaça da API aberta — as rotas respondem e o JSON é válido mesmo nas
linhas em que gap/ieas são NaN (município-anos cinza, sem cobertura mínima)."""

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from farol_ss import config
from farol_ss.api.main import api
from farol_ss.io import duck

client = TestClient(api)

pytestmark = pytest.mark.skipif(
    not duck.exists(config.GOLD, "ieas"), reason="camada gold não gerada (rode make all)"
)


def test_municipios_lista_185():
    r = client.get("/municipios")
    assert r.status_code == 200
    assert len(r.json()) == 185


def test_municipio_inexistente_404():
    assert client.get("/municipios/9999999").status_code == 404


def test_ieas_json_valido_com_nan():
    r = client.get("/ieas")
    assert r.status_code == 200
    linhas = r.json()
    assert len(linhas) == 925
    # onde o farol é cinza (cobertura insuficiente), gap/ieas são NaN — o
    # encoder tem de emitir null em vez de quebrar com "Out of range float".
    cinza = [linha for linha in linhas if linha["farol"] == "cinza"]
    assert cinza, "esperava ao menos um município-ano cinza no recorte"
    assert all(linha["gap"] is None and linha["ieas"] is None for linha in cinza)


def test_formato_csv():
    r = client.get("/ieas?ano=2024&formato=csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    df = pd.read_csv(pd.io.common.StringIO(r.text))
    assert len(df) == 185


def test_fontes_tem_link_dados_gov():
    linhas = client.get("/fontes").json()
    assert any(l["dados_gov"].startswith("https://dados.gov.br") for l in linhas)

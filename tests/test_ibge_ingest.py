"""Regressão do bug de corrupção de código IBGE na ingestão de população.

Uma versão anterior de `_extrair_serie_populacao` reconstruía o cod_ibge com
`.lstrip("260")`, que corrompia 22 dos 185 municípios de PE (ex.: Bodocó
2602001 virava 2600001, código de outro município) porque `lstrip` remove
caracteres soltos, não um prefixo. Estes testes fixam o comportamento
correto: usar o id da API tal como vem, sem reconstrução manual.
"""

import math

import pandas as pd

from farol_ss.ingest.ibge import _extrair_serie_populacao, _interpolar_populacao


def _resposta_ibge(cod_ibge: str, ano: int, valor: int) -> list:
    """Mimetiza o formato de resposta do agregado 6579 do IBGE."""
    return [
        {
            "resultados": [
                {
                    "series": [
                        {
                            "localidade": {"id": cod_ibge},
                            "serie": {str(ano): str(valor)},
                        }
                    ]
                }
            ]
        }
    ]


def test_extrai_sem_corromper_codigo():
    """Bodocó (2602001) é o caso que a versão antiga corrompia para 2600001."""
    data = _resposta_ibge("2602001", 2024, 38000)
    serie = _extrair_serie_populacao(data, 2024)
    assert serie == {"2602001": 38000}


def test_extrai_todos_os_codigos_problematicos():
    """Reconstrução por lstrip falhava para 22/185 municípios — checar uma
    amostra deles diretamente, não só Bodocó."""
    problematicos = ["2602001", "2602100", "2602209", "2602605", "2610004"]
    for cod in problematicos:
        data = _resposta_ibge(cod, 2024, 12345)
        serie = _extrair_serie_populacao(data, 2024)
        assert cod in serie, f"{cod} não sobreviveu à extração"


def test_ignora_municipio_fora_do_recorte():
    # 3550308 = São Paulo; não é de PE
    data = _resposta_ibge("3550308", 2024, 12000000)
    assert _extrair_serie_populacao(data, 2024) == {}


def test_ignora_valor_reticencias():
    """IBGE usa "..." para marcar dado ausente; não é população zero."""
    data = _resposta_ibge("2611606", 2024, 0)
    data[0]["resultados"][0]["series"][0]["serie"]["2024"] = "..."
    assert _extrair_serie_populacao(data, 2024) == {}


def test_interpolacao_preenche_ano_ausente_marcando_a_fonte():
    df = pd.DataFrame(
        [
            {"cod_ibge": "2611606", "ano": 2021, "populacao": 1_600_000, "fonte_dado": "ibge"},
            {"cod_ibge": "2611606", "ano": 2024, "populacao": 1_630_000, "fonte_dado": "ibge"},
        ]
    )
    out = _interpolar_populacao(df, anos=[2021, 2022, 2023, 2024], faltantes=[2022, 2023])

    interpolados = out[out.fonte_dado == "interpolado"].set_index("ano")["populacao"]
    assert math.isclose(interpolados[2022], 1_610_000, abs_tol=1)
    assert math.isclose(interpolados[2023], 1_620_000, abs_tol=1)
    # dado original não é sobrescrito nem remarcado
    assert (out[out.ano == 2021]["fonte_dado"] == "ibge").all()

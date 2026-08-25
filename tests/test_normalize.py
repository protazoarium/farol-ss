"""normalize.py sustenta o IEAS inteiro — bugs aqui se propagam pra tudo."""

import numpy as np
import pandas as pd
import pytest

from farol_ss.index.normalize import media_ponderada, rank_percentil


def test_rank_percentil_em_zero_um():
    s = pd.Series([10, 20, 30, 40, 50])
    r = rank_percentil(s)
    assert r.min() == pytest.approx(0.2)
    assert r.max() == 1.0
    assert (r >= 0).all() and (r <= 1).all()


def test_rank_percentil_maior_valor_gera_maior_rank():
    s = pd.Series([5, 1, 3])
    r = rank_percentil(s)
    assert r[0] > r[2] > r[1]


def test_rank_percentil_preserva_nan():
    s = pd.Series([10, np.nan, 30])
    r = rank_percentil(s)
    assert r.isna()[1]
    assert r.notna()[0] and r.notna()[2]


def test_rank_percentil_serie_constante_nao_quebra():
    s = pd.Series([7, 7, 7, 7])
    r = rank_percentil(s)
    assert (r == 0.5).all()


def test_rank_percentil_todos_nan():
    s = pd.Series([np.nan, np.nan])
    r = rank_percentil(s)
    assert r.isna().all()


def test_media_ponderada_sem_faltantes():
    df = pd.DataFrame({"a": [1.0, 2.0], "b": [3.0, 4.0]})
    out = media_ponderada(df, {"a": 0.5, "b": 0.5})
    assert out[0] == pytest.approx(2.0)
    assert out[1] == pytest.approx(3.0)


def test_media_ponderada_renormaliza_quando_falta_componente():
    """Uma linha com 'b' ausente deve usar só 'a', não tratar 'b' como 0."""
    df = pd.DataFrame({"a": [10.0], "b": [np.nan]})
    out = media_ponderada(df, {"a": 0.4, "b": 0.6})
    # Sem renormalização ingênua (0.4*10 + 0.6*0 = 4), o resultado seria 4.
    # Com renormalização, só resta 'a', então o resultado é o próprio valor.
    assert out[0] == pytest.approx(10.0)


def test_media_ponderada_todas_faltantes_vira_nan():
    df = pd.DataFrame({"a": [np.nan], "b": [np.nan]})
    out = media_ponderada(df, {"a": 0.5, "b": 0.5})
    assert out.isna()[0]


def test_media_ponderada_coluna_ausente_leva_erro_claro():
    df = pd.DataFrame({"a": [1.0]})
    with pytest.raises(KeyError):
        media_ponderada(df, {"a": 0.5, "b": 0.5})

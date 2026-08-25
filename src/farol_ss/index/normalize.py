"""Normalização por rank percentil — a métrica comum do IEAS.

Rank percentil (não z-score) por ser robusto a outliers e não assumir
distribuição normal: um único município com gasto per capita 50x a mediana
(comum em municípios pequenos com um hospital regional) não deve esmagar a
escala dos outros 184.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def rank_percentil(serie: pd.Series) -> pd.Series:
    """Converte uma série para rank percentil em [0, 1].

    NaN permanece NaN (não é preenchido com 0.5 nem descartado — quem chama
    decide o que fazer com a ausência, normalmente via a regra do cinza).
    Série constante (todos os valores iguais) devolve 0.5 para todo mundo,
    em vez de division-by-zero ou NaN — não há ordenação a extrair de valores
    idênticos, mas isso não deveria derrubar o cálculo.
    """
    if serie.notna().sum() == 0:
        return pd.Series(np.nan, index=serie.index)
    if serie.nunique(dropna=True) == 1:
        # 0.0 * NaN é NaN (IEEE 754), não 0 — não dá pra combinar os dois
        # casos numa única expressão aritmética; onde()/mask() explícito.
        return pd.Series(0.5, index=serie.index).where(serie.notna())

    return serie.rank(pct=True, na_option="keep")


def media_ponderada(df: pd.DataFrame, pesos: dict[str, float]) -> pd.Series:
    """Média ponderada tolerante a NaN: re-normaliza os pesos pelos
    componentes presentes em cada linha, em vez de propagar NaN quando falta
    um componente.

    Isso é o que permite ao subíndice de necessidade funcionar mesmo com o
    SIH bloqueado (peso redistribuído em conf/ieas.yml) e, de forma mais
    geral, permite que um município com uma fonte faltante ainda tenha os
    outros componentes computados — desde que a cobertura mínima do eixo,
    verificada à parte, seja respeitada.
    """
    cols = list(pesos.keys())
    faltantes = [c for c in cols if c not in df.columns]
    if faltantes:
        raise KeyError(f"colunas ausentes no DataFrame: {faltantes}")

    valores = df[cols].astype(float)
    pesos_arr = pd.Series(pesos)

    mascara = valores.notna()
    peso_efetivo = mascara.mul(pesos_arr, axis=1)
    soma_pesos = peso_efetivo.sum(axis=1)

    numerador = valores.fillna(0.0).mul(pesos_arr, axis=1).sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        resultado = numerador / soma_pesos

    resultado[soma_pesos == 0] = np.nan
    return resultado

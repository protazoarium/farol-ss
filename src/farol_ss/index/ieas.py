"""IEAS — Índice de Efetividade da Alocação Sanitária.

Dois eixos (N = necessidade, A = alocação), cada um um rank percentil em
[0, 1] dentro de PE. `gap = rank(A) - rank(N)` é o que colore o farol —
negativo significa que a alocação fica atrás da necessidade. `ieas = 1 -
|gap|` é o score de alinhamento, usado só para ranquear, não para colorir
(um gap muito positivo e um muito negativo têm o mesmo |gap|, mas significam
coisas opostas — por isso o farol usa o `gap` com sinal, nunca o `ieas`).

A regra do cinza é aplicada por cobertura, não por linha individual: um eixo
cuja fração de componentes presentes cai abaixo do limiar em
`conf/ieas.yml` (`cobertura_minima`) vira NaN inteiro para aquele
município-ano, e a cor final é "cinza" — nunca um número calculado sobre
dado majoritariamente ausente.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from farol_ss.config import ieas_conf
from farol_ss.index.normalize import media_ponderada, rank_percentil


def _cobertura_por_eixo(df: pd.DataFrame, colunas: list[str]) -> pd.Series:
    """Fração das colunas do eixo presentes (não-NaN) em cada linha."""
    return df[colunas].notna().mean(axis=1)


def calcular_necessidade(df: pd.DataFrame) -> pd.DataFrame:
    """Eixo N: epidemiológico + saneamento + vulnerabilidade → rank percentil.

    Espera colunas normalizadas em [0,1] por subíndice: `sub_epidemiologico`,
    `sub_saneamento`, `sub_vulnerabilidade` (cada uma já calculada por quem
    chama, a partir dos indicadores brutos — ver `montar_subindices_exemplo`
    para a forma esperada). Este módulo não sabe de onde vêm os indicadores
    brutos; só combina o que já foi normalizado, o que o mantém testável com
    fixtures sintéticas sem depender do pipeline de ingestão inteiro.
    """
    conf = ieas_conf()["necessidade"]
    subcols = ["sub_epidemiologico", "sub_saneamento", "sub_vulnerabilidade"]

    cobertura = _cobertura_por_eixo(df, subcols)
    minimo = ieas_conf()["cobertura_minima"]["necessidade"]

    necessidade_bruta = media_ponderada(
        df,
        {
            "sub_epidemiologico": conf["pesos"]["epidemiologico"],
            "sub_saneamento": conf["pesos"]["saneamento"],
            "sub_vulnerabilidade": conf["pesos"]["vulnerabilidade"],
        },
    )
    necessidade_bruta[cobertura < minimo] = np.nan

    out = df.copy()
    out["necessidade_bruta"] = necessidade_bruta
    out["necessidade_rank"] = rank_percentil(necessidade_bruta)
    out["necessidade_cobertura"] = cobertura
    return out


def calcular_alocacao(df: pd.DataFrame) -> pd.DataFrame:
    """Eixo A: L1 + L2 + L3 per capita deflacionado → rank percentil.

    Espera `l1_per_capita`, `l2_per_capita`, `l3_per_capita` já deflacionados
    para o ano-base (ver conf/ieas.yml `recorte.ano_base_deflacao`).
    """
    conf = ieas_conf()["alocacao"]
    subcols = ["l1_per_capita", "l2_per_capita", "l3_per_capita"]

    cobertura = _cobertura_por_eixo(df, subcols)
    minimo = ieas_conf()["cobertura_minima"]["alocacao"]

    alocacao_bruta = media_ponderada(
        df,
        {
            "l1_per_capita": conf["pesos"]["l1_repasse_federal"],
            "l2_per_capita": conf["pesos"]["l2_execucao_propria"],
            "l3_per_capita": conf["pesos"]["l3_contratacao_insumos"],
        },
    )
    alocacao_bruta[cobertura < minimo] = np.nan

    out = df.copy()
    out["alocacao_bruta"] = alocacao_bruta
    out["alocacao_rank"] = rank_percentil(alocacao_bruta)
    out["alocacao_cobertura"] = cobertura
    return out


def classificar_farol(gap: pd.Series) -> pd.Series:
    """Aplica os limiares do semáforo. NaN em `gap` vira 'cinza'."""
    conf = ieas_conf()["farol"]
    cond = [
        gap.isna(),
        gap <= conf["vermelho_ate"],
        gap <= conf["amarelo_ate"],
        gap <= conf["verde_ate"],
        gap >= conf["azul_a_partir"],
    ]
    escolhas = ["cinza", "vermelho", "amarelo", "verde", "azul"]
    # np.select avalia em ordem: a primeira condição verdadeira vence, por
    # isso vermelho/amarelo (mais restritivos) vêm antes de verde (mais
    # abrangente) na lista. A zona entre verde_ate e azul_a_partir não bate
    # em nenhuma condição explícita e cai no default — que por isso também é
    # 'verde', não um valor arbitrário.
    return pd.Series(np.select(cond, escolhas, default="verde"), index=gap.index)


def calcular_ieas(df: pd.DataFrame) -> pd.DataFrame:
    """Pipeline completo: necessidade + alocação → gap, ieas, farol."""
    out = calcular_necessidade(df)
    out = calcular_alocacao(out)

    out["gap"] = out["alocacao_rank"] - out["necessidade_rank"]
    out["ieas"] = 1 - out["gap"].abs()
    out["farol"] = classificar_farol(out["gap"])
    return out

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

**Normalização por ano.** Quando o DataFrame traz a coluna `ano`, todo ranque é
calculado *dentro de cada ano* (os 185 municípios de um mesmo ano), e não sobre
os 925 município-anos empilhados. Ranquear a tabela empilhada faz o gap medir
mudanças de nível entre anos (p. ex. a mediana de L1 mais que dobra de 2022 para
2023), e não o alinhamento entre municípios. Consequência declarada: o gap
médio é nulo por construção em cada ano — o semáforo é uma medida *relativa
dentro do ano* e não diz se a alocação do estado melhorou ou piorou.

**Eixo A.** Por padrão, o índice usa os componentes listados em
`conf/ieas.yml::alocacao.componentes_no_indice` (L1 e L2). L3 (PNCP) fica fora
da composição principal porque sua cobertura cresce no período (0 município-ano
completo em 2020; 156 em 2024) e faria o mesmo município mudar de ranque só
porque o PNCP passou a cobri-lo; entra como análise de sensibilidade.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from farol_ss.config import ieas_conf
from farol_ss.index.normalize import media_ponderada, normalizar

_ARBOVIROSES = ("taxa_deng", "taxa_chik", "taxa_zika")
_VEICULACAO_HIDRICA = ("taxa_lept", "taxa_hepa", "taxa_esqu")


def _grupos(df: pd.DataFrame, por_ano: bool) -> pd.Series | None:
    """Série de agrupamento (o ano) ou None quando não há `ano` ou por_ano=False."""
    return df["ano"] if (por_ano and "ano" in df.columns) else None


def montar_sub_epidemiologico(
    df: pd.DataFrame, *, por_ano: bool = True, metodo: str = "ranque"
) -> pd.Series:
    """Subíndice epidemiológico do eixo Necessidade, em [0, 1].

    Três componentes, cada um um rank percentil dentro de PE, combinados com os
    pesos de `conf/ieas.yml::necessidade.epidemiologico.pesos`:

    - **arboviroses**: rank da soma das taxas de dengue + chikungunya + zika;
    - **veiculação hídrica**: rank da soma das taxas de leptospirose +
      hepatite A + esquistossomose (SINAN);
    - **internações por saneamento (DRSAI)**: rank da taxa de internações do
      SIH cujo diagnóstico é doença relacionada a saneamento ambiental
      inadequado (ver `ingest/sih.py`).

    A soma-antes-do-rank (em vez de média de ranks) dá a um município com carga
    alta em vários agravos a posição que ele de fato ocupa, sem diluir.
    """
    pesos = ieas_conf()["necessidade"]["epidemiologico"]["pesos"]
    comp = pd.DataFrame(index=df.index)
    g = _grupos(df, por_ano)

    def rk(x: pd.Series) -> pd.Series:
        return normalizar(x, g, metodo)

    arbo = [c for c in _ARBOVIROSES if c in df.columns]
    comp["arboviroses"] = rk(df[arbo].sum(axis=1)) if arbo else np.nan

    hidr = [c for c in _VEICULACAO_HIDRICA if c in df.columns]
    comp["veiculacao_hidrica"] = rk(df[hidr].sum(axis=1)) if hidr else np.nan

    if "taxa_internacoes_drsai" in df.columns:
        comp["internacoes_saneamento"] = rk(df["taxa_internacoes_drsai"])
    else:
        comp["internacoes_saneamento"] = np.nan

    return media_ponderada(comp, {k: pesos[k] for k in comp.columns if k in pesos})


def montar_subindices(
    df: pd.DataFrame, *, por_ano: bool = True, metodo: str = "ranque"
) -> pd.DataFrame:
    """Acrescenta `sub_epidemiologico`, `sub_vulnerabilidade` e `sub_saneamento`.

    Cada subíndice é normalizado dentro do ano (`por_ano=True`). Fica aqui, e
    não no CLI, para que a análise de sensibilidade use exatamente o mesmo
    código do índice publicado.
    """
    out = df.copy()
    g = _grupos(out, por_ano)
    out["sub_epidemiologico"] = montar_sub_epidemiologico(out, por_ano=por_ano, metodo=metodo)
    for destino, origem in (
        ("sub_vulnerabilidade", "extrema_pobreza_por_mil_hab"),
        ("sub_saneamento", "sub_saneamento_bruto"),
    ):
        out[destino] = normalizar(out[origem], g, metodo) if origem in out.columns else np.nan
    return out


def _cobertura_por_eixo(df: pd.DataFrame, colunas: list[str]) -> pd.Series:
    """Fração das colunas do eixo presentes (não-NaN) em cada linha."""
    return df[colunas].notna().mean(axis=1)


def calcular_necessidade(
    df: pd.DataFrame,
    *,
    por_ano: bool = True,
    metodo: str = "ranque",
    pesos: dict[str, float] | None = None,
) -> pd.DataFrame:
    """Eixo N: epidemiológico + saneamento + vulnerabilidade → rank percentil.

    Espera colunas normalizadas em [0,1] por subíndice: `sub_epidemiologico`,
    `sub_saneamento`, `sub_vulnerabilidade` (ver `montar_subindices`). Este
    módulo só combina o que já foi normalizado, o que o mantém testável com
    fixtures sintéticas sem depender do pipeline de ingestão inteiro.

    `pesos` (chaves `epidemiologico`/`saneamento`/`vulnerabilidade`) substitui
    os de `conf/ieas.yml` — usado apenas na análise de sensibilidade.
    """
    p = pesos or ieas_conf()["necessidade"]["pesos"]
    subcols = ["sub_epidemiologico", "sub_saneamento", "sub_vulnerabilidade"]

    cobertura = _cobertura_por_eixo(df, subcols)
    minimo = ieas_conf()["cobertura_minima"]["necessidade"]

    necessidade_bruta = media_ponderada(
        df,
        {
            "sub_epidemiologico": p["epidemiologico"],
            "sub_saneamento": p["saneamento"],
            "sub_vulnerabilidade": p["vulnerabilidade"],
        },
    )
    necessidade_bruta[cobertura < minimo] = np.nan

    out = df.copy()
    out["necessidade_bruta"] = necessidade_bruta
    out["necessidade_rank"] = normalizar(necessidade_bruta, _grupos(df, por_ano), metodo)
    out["necessidade_cobertura"] = cobertura
    return out


_COLUNA_ALOCACAO = {
    "l1_repasse_federal": "l1_per_capita",
    "l2_execucao_propria": "l2_per_capita",
    "l3_contratacao_insumos": "l3_per_capita",
}


def calcular_alocacao(
    df: pd.DataFrame,
    *,
    por_ano: bool = True,
    metodo: str = "ranque",
    pesos: dict[str, float] | None = None,
    componentes: list[str] | None = None,
) -> pd.DataFrame:
    """Eixo A: componentes per capita deflacionados → rank percentil.

    Espera `l1_per_capita`, `l2_per_capita` e `l3_per_capita` já deflacionados
    para o ano-base (ver conf/ieas.yml `recorte.ano_base_deflacao`). Só entram
    no índice os `componentes` (padrão: `alocacao.componentes_no_indice`); a
    cobertura do eixo é medida sobre esses mesmos componentes, e os pesos são
    renormalizados entre eles.
    """
    conf = ieas_conf()["alocacao"]
    p = pesos or conf["pesos"]
    usados = componentes or conf.get("componentes_no_indice") or list(_COLUNA_ALOCACAO)
    subcols = [_COLUNA_ALOCACAO[c] for c in usados]

    cobertura = _cobertura_por_eixo(df, subcols)
    minimo = ieas_conf()["cobertura_minima"]["alocacao"]

    alocacao_bruta = media_ponderada(df, {_COLUNA_ALOCACAO[c]: p[c] for c in usados})
    alocacao_bruta[cobertura < minimo] = np.nan
    # Piso absoluto de componentes (nunca mais que o número de componentes em uso).
    piso = min(ieas_conf()["cobertura_minima"].get("alocacao_min_componentes", 1), len(subcols))
    alocacao_bruta[df[subcols].notna().sum(axis=1) < piso] = np.nan

    out = df.copy()
    out["alocacao_bruta"] = alocacao_bruta
    out["alocacao_rank"] = normalizar(alocacao_bruta, _grupos(df, por_ano), metodo)
    out["alocacao_cobertura"] = cobertura
    return out


def classificar_farol(gap: pd.Series, limiares: dict[str, float] | None = None) -> pd.Series:
    """Aplica os limiares do semáforo. NaN em `gap` vira 'cinza'."""
    conf = limiares or ieas_conf()["farol"]
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


def calcular_ieas(
    df: pd.DataFrame,
    *,
    por_ano: bool = True,
    metodo: str = "ranque",
    pesos_n: dict[str, float] | None = None,
    pesos_a: dict[str, float] | None = None,
    componentes_a: list[str] | None = None,
    limiares: dict[str, float] | None = None,
) -> pd.DataFrame:
    """Pipeline completo: necessidade + alocação → gap, ieas, farol.

    Os argumentos nomeados existem para a análise de sensibilidade; sem eles o
    resultado é o índice publicado (parâmetros de `conf/ieas.yml`).
    """
    out = calcular_necessidade(df, por_ano=por_ano, metodo=metodo, pesos=pesos_n)
    out = calcular_alocacao(
        out, por_ano=por_ano, metodo=metodo, pesos=pesos_a, componentes=componentes_a
    )

    out["gap"] = out["alocacao_rank"] - out["necessidade_rank"]
    out["ieas"] = 1 - out["gap"].abs()
    out["farol"] = classificar_farol(out["gap"], limiares)
    return out

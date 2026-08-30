"""Monta o fato único (cod_ibge, ano) — grão canônico do projeto.

Parte de uma grade completa 185 municípios × anos do recorte (mesmo que uma
fonte não tenha dado para todo mundo, o município continua existindo na
grade — é isso que permite a regra do cinza: "sem dado" é visível, não
ausente da tabela). Cada fonte entra como um LEFT JOIN nessa grade.

Como as fontes vão ficando prontas incrementalmente (SIOPS, SNIS e CadÚnico
ainda não estão implementados — ver docs/spike-fontes.md), este módulo junta
o que existe em silver/ e preenche o resto com NULL, sem falhar. A cobertura
de cada indicador vai para uma coluna `cobertura_<indicador>` que o IEAS usa
para decidir a regra do cinza.
"""

from __future__ import annotations

import pandas as pd

from farol_ss import config
from farol_ss.io import duck
from farol_ss.io import municipios as M


def _grade_base() -> pd.DataFrame:
    """185 municípios × anos do recorte — a espinha dorsal do gold."""
    muns = M.municipios()[["cod_ibge"]]
    anos = pd.DataFrame({"ano": config.anos()})
    return muns.merge(anos, how="cross")


def _juntar_populacao(base: pd.DataFrame) -> pd.DataFrame:
    if not duck.exists(config.SILVER, "ibge_populacao"):
        base["populacao"] = pd.NA
        base["populacao_fonte"] = pd.NA
        return base
    pop = duck.read_silver("ibge_populacao")
    out = base.merge(pop, on=["cod_ibge", "ano"], how="left")
    return out.rename(columns={"fonte_dado": "populacao_fonte"})


def _juntar_epidemiologia(base: pd.DataFrame) -> pd.DataFrame:
    """Pivota agravo→colunas e calcula taxa por 100 mil habitantes."""
    if not duck.exists(config.SILVER, "epidemiologia"):
        return base

    epi = duck.read_silver("epidemiologia")
    pivot = epi.pivot_table(
        index=["cod_ibge", "ano"], columns="agravo", values="casos", aggfunc="sum", fill_value=0
    )
    pivot.columns = [f"casos_{c.lower()}" for c in pivot.columns]
    pivot = pivot.reset_index()

    out = base.merge(pivot, on=["cod_ibge", "ano"], how="left")
    casos_cols = [c for c in out.columns if c.startswith("casos_")]
    # Município sem notificação = 0 casos (dado real), não NULL (dado ausente)
    out[casos_cols] = out[casos_cols].fillna(0)

    if "populacao" in out.columns:
        for c in casos_cols:
            out[c.replace("casos_", "taxa_")] = out[c] / out["populacao"] * 100_000

    return out


def _deflator_por_ano() -> dict[int, float]:
    """Fator que leva R$ de cada ano ao poder de compra do ano-base (IPCA).

    Usa a média anual do número-índice mensal do IPCA (agregado 1737). Um
    valor de 2022 multiplicado por `deflator[2022]` fica em R$ de
    `conf/ieas.yml::recorte.ano_base_deflacao`.
    """
    ipca = duck.read_silver("ibge_ipca")
    ipca = ipca.assign(ano=ipca["ano_mes"].str[:4].astype(int))
    media_anual = ipca.groupby("ano")["ipca"].mean()
    base = config.recorte()["ano_base_deflacao"]
    ref = media_anual.get(base, media_anual.iloc[-1])
    return (ref / media_anual).to_dict()


def _juntar_l3_pncp(base: pd.DataFrame) -> pd.DataFrame:
    """Camada L3 — contratação de insumos (PNCP), deflacionada para o ano-base."""
    if not duck.exists(config.SILVER, "pncp"):
        base["l3_total"] = pd.NA
        base["l3_per_capita"] = pd.NA
        return base

    pncp = duck.read_silver("pncp")
    # valor homologado é o efetivamente contratado; quando ausente (compra em
    # andamento), cai para o estimado, marcando que houve processo.
    valor = pncp["valor_total_homologado"].fillna(pncp["valor_total_estimado"])
    l3 = (
        pncp.assign(valor=valor)
        .dropna(subset=["cod_ibge", "ano"])
        .groupby(["cod_ibge", "ano"], as_index=False)["valor"]
        .sum()
        .rename(columns={"valor": "_l3_nominal"})
    )
    l3["ano"] = l3["ano"].astype(int)

    out = base.merge(l3, on=["cod_ibge", "ano"], how="left")
    deflator = _deflator_por_ano()
    out["l3_total"] = out["_l3_nominal"] * out["ano"].map(deflator)
    if "populacao" in out.columns:
        out["l3_per_capita"] = out["l3_total"] / out["populacao"]
    return out.drop(columns=["_l3_nominal"])


def _juntar_l2_siops(base: pd.DataFrame) -> pd.DataFrame:
    """Camada L2 — execução própria municipal em saúde (SIOPS).

    `l2_rec_proprios_per_capita` vem em R$ correntes do ano; aqui é
    deflacionado para o ano-base. `pct_receita_propria_saude` (piso EC 29/15%)
    é razão, não passa por deflação.
    """
    if not duck.exists(config.SILVER, "siops"):
        base["l2_per_capita"] = pd.NA
        base["l2_pct_receita_saude"] = pd.NA
        return base

    siops = duck.read_silver("siops")
    siops["ano"] = siops["ano"].astype(int)
    out = base.merge(
        siops[["cod_ibge", "ano", "l2_rec_proprios_per_capita", "pct_receita_propria_saude"]],
        on=["cod_ibge", "ano"],
        how="left",
    )
    deflator = _deflator_por_ano()
    out["l2_per_capita"] = out["l2_rec_proprios_per_capita"] * out["ano"].map(deflator)
    out["l2_pct_receita_saude"] = out["pct_receita_propria_saude"]
    return out.drop(columns=["l2_rec_proprios_per_capita", "pct_receita_propria_saude"])


def _juntar_l1_transparencia(base: pd.DataFrame) -> pd.DataFrame:
    """Camada L1 — repasse federal (parcial): transferências sociais federais
    por município (Portal da Transparência). Valor mensal de junho → anual
    (×12) e deflacionado. Ver `ingest/transparencia.py` para a limitação."""
    if not duck.exists(config.SILVER, "transparencia"):
        base["l1_per_capita"] = pd.NA
        return base

    tr = duck.read_silver("transparencia")
    tr["ano"] = tr["ano"].astype(int)
    out = base.merge(
        tr[["cod_ibge", "ano", "l1_transf_sociais_mes"]], on=["cod_ibge", "ano"], how="left"
    )
    deflator = _deflator_por_ano()
    l1_anual = out["l1_transf_sociais_mes"] * 12 * out["ano"].map(deflator)
    if "populacao" in out.columns:
        out["l1_per_capita"] = l1_anual / out["populacao"]
    return out.drop(columns=["l1_transf_sociais_mes"])


def _juntar_financeiro(base: pd.DataFrame) -> pd.DataFrame:
    """Eixo Alocação: L1 (Transparência, parcial) + L2 (SIOPS) + L3 (PNCP)."""
    base = _juntar_l3_pncp(base)
    base = _juntar_l2_siops(base)
    base = _juntar_l1_transparencia(base)
    return base


def _juntar_saneamento(base: pd.DataFrame) -> pd.DataFrame:
    """Subíndice de saneamento (eixo Necessidade) — Censo 2022 do IBGE.

    `sub_saneamento_bruto` já é o déficit ponderado (água/esgoto/lixo) calculado
    na ingestão a partir dos pesos de `conf/ieas.yml`. É um retrato de 2022
    aplicado a todos os anos do recorte (o SNIS, que era anual, foi encerrado).
    """
    path_name = "ibge_saneamento"
    if not duck.exists(config.SILVER, path_name):
        base["sub_saneamento_bruto"] = pd.NA
        return base

    san = duck.read_silver(path_name)[["cod_ibge", "sub_saneamento_bruto"]]
    return base.merge(san, on="cod_ibge", how="left")


def _juntar_vulnerabilidade(base: pd.DataFrame) -> pd.DataFrame:
    """Subíndice de vulnerabilidade (eixo Necessidade) — CadÚnico via SAGI.

    `extrema_pobreza_por_mil_hab` = famílias em extrema pobreza / população
    (IBGE, já na grade) × 1000. A normalização por rank percentil fica no
    `index/ieas.py`, como nos demais subíndices.
    """
    if not duck.exists(config.SILVER, "cadunico"):
        base["extrema_pobreza_por_mil_hab"] = pd.NA
        return base

    cad = duck.read_silver("cadunico")
    cad["ano"] = cad["ano"].astype(int)
    out = base.merge(
        cad[["cod_ibge", "ano", "familias_extrema_pobreza", "familias_cadastradas"]],
        on=["cod_ibge", "ano"],
        how="left",
    )
    if "populacao" in out.columns:
        out["extrema_pobreza_por_mil_hab"] = (
            out["familias_extrema_pobreza"] / out["populacao"] * 1000
        )
    return out.drop(columns=["familias_extrema_pobreza"])


def montar() -> pd.DataFrame:
    base = _grade_base()
    base = _juntar_populacao(base)
    base = _juntar_epidemiologia(base)
    base = _juntar_financeiro(base)
    base = _juntar_vulnerabilidade(base)
    base = _juntar_saneamento(base)
    return base


def rodar() -> None:
    df = montar()
    duck.write_gold(df, "fato_municipio_ano")
    print(
        f"  ✓ gold/fato_municipio_ano: {len(df)} linhas ({df.cod_ibge.nunique()} municípios × {df.ano.nunique()} anos)"
    )

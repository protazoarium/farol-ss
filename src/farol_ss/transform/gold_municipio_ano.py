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


def montar() -> pd.DataFrame:
    base = _grade_base()
    base = _juntar_populacao(base)
    base = _juntar_epidemiologia(base)
    # TODO próximas fontes conforme forem ficando prontas:
    #   _juntar_financeiro (PNCP L3, SIOPS L2, Transparência L1)
    #   _juntar_saneamento (SNIS)
    #   _juntar_vulnerabilidade (CadÚnico)
    return base


def rodar() -> None:
    df = montar()
    duck.write_gold(df, "fato_municipio_ano")
    print(
        f"  ✓ gold/fato_municipio_ano: {len(df)} linhas ({df.cod_ibge.nunique()} municípios × {df.ano.nunique()} anos)"
    )

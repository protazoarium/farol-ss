"""Carregadores de dado do painel — leem o gold/ e o cacheiam.

Tudo é `@st.cache_data`: o pipeline grava Parquet uma vez, o painel lê uma
vez por sessão. Nenhuma página fala com o disco direto.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
from shapely import wkb
from shapely.geometry import mapping

from farol_ss import config
from farol_ss.io import duck
from farol_ss.io import municipios as M


@st.cache_data(show_spinner=False)
def ieas() -> pd.DataFrame:
    """Fato município × ano com IEAS, gap e farol (ver `farol ieas`)."""
    df = duck.read_gold("ieas")
    dim = M.municipios()[["cod_ibge", "nome", "mesorregiao", "regiao_intermediaria"]]
    return df.merge(dim, on="cod_ibge", how="left")


@st.cache_data(show_spinner=False)
def alertas() -> pd.DataFrame:
    """Alertas de desalinhamento estrutural, ou vazio se ainda não há cor."""
    if not duck.exists(config.GOLD, "alertas"):
        return pd.DataFrame(columns=["cod_ibge", "ano", "tipo", "severidade", "explicacao"])
    return duck.read_gold("alertas")


@st.cache_data(show_spinner=False)
def malhas_geojson() -> dict:
    """Malha municipal de PE (IBGE) como GeoJSON, uma feature por município.

    O bronze guarda a geometria como WKB; aqui vira GeoJSON no CRS 4326 que
    o folium consome direto. `id` de cada feature é o cod_ibge de 7 dígitos.
    Feito só com shapely (sem geopandas) para manter o deploy do painel leve.
    """
    raw = pd.read_parquet(config.BRONZE / "ibge_malhas.parquet")
    features = [
        {
            "type": "Feature",
            "id": str(cod),
            "properties": {"cod_ibge": str(cod)},
            "geometry": mapping(wkb.loads(geom)),
        }
        for cod, geom in zip(raw["cod_ibge"], raw["geometry"])
    ]
    return {"type": "FeatureCollection", "features": features}


@st.cache_data(show_spinner=False)
def epidemiologia() -> pd.DataFrame:
    """Notificações SINAN em formato longo (cod_ibge, ano, agravo, casos)."""
    return duck.read_silver("epidemiologia")


@st.cache_data(show_spinner=False)
def pncp() -> pd.DataFrame:
    """Contratações municipais do PNCP consolidadas, ou vazio se não ingerido."""
    if not duck.exists(config.SILVER, "pncp"):
        return pd.DataFrame()
    return duck.read_silver("pncp")


@st.cache_data(show_spinner=False)
def fontes() -> pd.DataFrame:
    """Catálogo de fontes × manifesto de coleta — ver `farol_ss.proveniencia`."""
    from farol_ss import proveniencia

    return proveniencia.tabela()


@st.cache_data(show_spinner=False)
def anos() -> list[int]:
    return sorted(int(a) for a in ieas()["ano"].unique())


def coropletico(ano: int, camada: str) -> pd.DataFrame:
    """Uma linha por município para o ano dado, com a coluna `valor` da camada.

    `farol` sai como categoria; as demais camadas saem como número. Sempre
    185 linhas — município sem dado na camada mantém `valor` NaN/cinza, que
    é o ponto: ausência visível, não linha sumida.
    """
    df = ieas()
    ano_df = df[df["ano"] == ano].copy()
    if camada == "farol":
        ano_df["valor"] = ano_df["farol"]
    else:
        ano_df["valor"] = pd.to_numeric(ano_df[camada], errors="coerce")
    return ano_df

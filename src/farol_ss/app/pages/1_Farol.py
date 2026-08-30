"""Página Farol — mapa coroplético dos 185 municípios de PE.

O IEAS só ganha cor quando os dois eixos alcançam a cobertura mínima de
`conf/ieas.yml`. Hoje isso não acontece (falta L1/Transparência, L2/SIOPS e
saneamento/SNIS — ver `docs/spike-fontes.md`), então a camada "Farol" sai
toda cinza — de propósito. Para a página ser útil já, o seletor de camada
deixa olhar os sub-índices que JÁ têm dado: a carga epidemiológica (SINAN) e
a contratação de insumos L3 (PNCP). Quando as fontes destravarem, a camada
"Farol" passa a colorir sozinha, sem mudar código aqui.
"""

from __future__ import annotations

import copy

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from farol_ss.app import dados, tema

st.set_page_config(
    page_title="Farol · Farol-SS",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🚦 Farol da alocação sanitária")
st.caption(
    "Cada município colorido pelo descompasso entre **necessidade** (carga de "
    "doença, déficit sanitário, vulnerabilidade) e **alocação** (R$/hab em "
    "saúde). Vermelho = necessidade não atendida."
)

# --- Filtros -------------------------------------------------------------
anos = dados.anos()
ano = st.sidebar.selectbox("Ano", anos, index=len(anos) - 1)
# Padrão: Necessidade — é a camada com dado real hoje (SINAN, 185/185). O
# farol fica cinza até L1/L2/saneamento entrarem, então abrir nele passaria
# uma tela vazia; a página começa mostrando algo interpretável.
camadas = list(tema.CAMADAS)
camada = st.sidebar.selectbox(
    "Camada",
    camadas,
    index=camadas.index("sub_epidemiologico"),
    format_func=lambda k: tema.CAMADAS[k],
)

df = dados.coropletico(ano, camada)

meso_opts = ["(todas)"] + sorted(df["mesorregiao"].dropna().unique())
meso = st.sidebar.selectbox("Mesorregião", meso_opts)
if meso != "(todas)":
    df = df[df["mesorregiao"] == meso]

categorico = camada == "farol"

# --- Faixa de valores da camada contínua -------------------------------
if not categorico:
    serie = df["valor"].dropna()
    vmin = float(serie.min()) if not serie.empty else 0.0
    vmax = float(serie.max()) if not serie.empty else 1.0


def _fmt(v: float) -> str:
    """Formata um valor da camada contínua conforme a unidade."""
    if camada == "l3_per_capita":
        return f"R$ {v:,.0f}/hab".replace(",", ".")
    return f"percentil {v:.0%}"  # sub_epidemiologico é rank ∈ [0, 1]


def _cor(cod: str) -> str:
    linha = df.loc[df["cod_ibge"] == cod]
    if linha.empty:
        return tema.CINZA_SEM_DADO
    v = linha["valor"].iloc[0]
    if categorico:
        return tema.FAROL_COR.get(v, tema.CINZA_SEM_DADO)
    return tema.cor_sequencial(v, vmin, vmax)


def _rotulo_valor(cod: str) -> str:
    linha = df.loc[df["cod_ibge"] == cod]
    if linha.empty:
        return "sem dado"
    v = linha["valor"].iloc[0]
    if categorico:
        return f"{tema.FAROL_ROTULO.get(v, v)}"
    if pd.isna(v):
        return "sem dado"
    return _fmt(v)


# --- KPIs --------------------------------------------------------------
n_total = df["cod_ibge"].nunique()
if categorico:
    com_cor = int((df["valor"] != "cinza").sum())
    k1, k2, k3 = st.columns(3)
    k1.metric("Municípios", n_total)
    k2.metric("Com IEAS calculado", com_cor)
    k3.metric("Cinza (sem cobertura)", n_total - com_cor)
    if com_cor == 0:
        st.info(
            "**Tudo cinza é o resultado correto hoje.** A regra do cinza "
            "(`conf/ieas.yml`) não deixa o IEAS ser calculado enquanto os dois "
            "eixos não têm cobertura mínima — falta o gasto L1 (Portal da "
            "Transparência, HTTP 403), L2 (SIOPS, sem API) e o saneamento (SNIS, "
            "DNS fora do ar). Troque a camada para ver o que já tem dado.",
            icon="ℹ️",
        )
else:
    com_dado = int(df["valor"].notna().sum())
    k1, k2, k3 = st.columns(3)
    k1.metric("Municípios", n_total)
    k2.metric("Com dado nesta camada", com_dado)
    k3.metric(
        "Cobertura",
        f"{com_dado / n_total:.0%}" if n_total else "—",
    )

# --- Mapa -------------------------------------------------------------
nome_por_cod = dados.ieas().drop_duplicates("cod_ibge").set_index("cod_ibge")["nome"].to_dict()
geojson = copy.deepcopy(dados.malhas_geojson())
for feat in geojson["features"]:
    cod = str(feat["id"])
    feat["properties"] = {
        "cod_ibge": cod,
        "nome": nome_por_cod.get(cod, cod),
        "valor": _rotulo_valor(cod),
    }

# OpenStreetMap: sem chave de API (o basemap CartoDB passou a exigir uma).
mapa = folium.Map(location=[-8.3, -37.6], zoom_start=7, tiles="OpenStreetMap")


def _style(feature: dict) -> dict:
    cod = str(feature["id"])
    dentro = cod in set(df["cod_ibge"])
    return {
        "fillColor": _cor(cod) if dentro else tema.CINZA_SEM_DADO,
        "color": tema.CONTORNO,
        "weight": 0.6,
        "fillOpacity": 0.85 if dentro else 0.15,
    }


folium.GeoJson(
    geojson,
    style_function=_style,
    highlight_function=lambda _f: {"weight": 2.2, "color": "#1a1a19"},
    tooltip=folium.GeoJsonTooltip(
        fields=["nome", "valor"],
        aliases=["Município", tema.CAMADAS[camada].split("—")[0].strip() + ":"],
        sticky=True,
    ),
).add_to(mapa)

col_mapa, col_leg = st.columns([4, 1])
with col_mapa:
    st_folium(mapa, height=560, use_container_width=True, returned_objects=[])

with col_leg:
    st.markdown("**Legenda**")
    if categorico:
        itens = [(tema.FAROL_COR[k], tema.FAROL_ROTULO[k]) for k in tema.FAROL_ORDEM]
    else:
        n = len(tema.SEQ_AZUL)
        passo = (vmax - vmin) / n
        itens = [(tema.SEQ_AZUL[k], f"≥ {_fmt(vmin + k * passo)}") for k in range(n)]
        itens.append((tema.CINZA_SEM_DADO, "sem dado"))
    linhas = "".join(
        f'<div style="display:flex;align-items:center;gap:6px;margin:2px 0">'
        f'<span style="width:14px;height:14px;background:{cor};'
        f'border:1px solid {tema.CONTORNO};display:inline-block;flex:none"></span>'
        f'<span style="font-size:0.8rem">{rot}</span></div>'
        for cor, rot in itens
    )
    st.markdown(linhas, unsafe_allow_html=True)

# --- Tabela (identidade nunca só por cor) -----------------------------
with st.expander("Ver tabela"):
    cols = ["cod_ibge", "nome", "mesorregiao", "valor"]
    tab = df[cols].rename(
        columns={
            "cod_ibge": "Cód. IBGE",
            "nome": "Município",
            "mesorregiao": "Mesorregião",
            "valor": tema.CAMADAS[camada].split("—")[0].strip(),
        }
    )
    ordenar = tab.columns[-1]
    tab = tab.sort_values(ordenar, ascending=categorico, na_position="last")
    st.dataframe(tab, width="stretch", hide_index=True)
    st.download_button(
        "Baixar CSV",
        tab.to_csv(index=False).encode("utf-8"),
        file_name=f"farol_{camada}_{ano}.csv",
        mime="text/csv",
    )

# --- Alertas do ano (resumo; detalhe na página Alertas) --------------
al = dados.alertas()
al = al[al["ano"] == ano] if not al.empty else al
if not al.empty:
    st.subheader(f"Alertas em {ano}")
    dim = dados.ieas().drop_duplicates("cod_ibge").set_index("cod_ibge")["nome"]
    al = al.assign(município=al["cod_ibge"].map(dim))
    st.dataframe(
        al[["município", "tipo", "severidade", "explicacao"]].rename(
            columns={"tipo": "Tipo", "severidade": "Severidade", "explicacao": "Explicação"}
        ),
        width="stretch",
        hide_index=True,
    )
    st.caption("Detalhe e filtros na página **Alertas** (menu lateral).")

st.caption(
    "Fonte: SINAN/DATASUS (epidemiologia), PNCP (compras L3), IBGE (população, "
    "malha). Metodologia completa em `docs/` e `conf/ieas.yml`."
)

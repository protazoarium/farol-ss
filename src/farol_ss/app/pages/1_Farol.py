"""Página Farol — mapa coroplético dos 185 municípios de PE.

O IEAS ganha cor quando os dois eixos alcançam a cobertura mínima de
`conf/ieas.yml`. Com o L1 (Transparência) completo, os dois eixos têm cobertura
para 921 dos 925 município-anos; o cinza que resta é o Distrito Estadual de
Fernando de Noronha (sem SIOPS nem PNCP municipais). O seletor de camada abre
cada subíndice isolado — carga epidemiológica, saneamento, vulnerabilidade, cada
camada de alocação — além do Farol combinado.
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
tema.aplicar_estilo()

tema.cabecalho(
    "🚦 Farol da alocação sanitária",
    "Cada município colorido pelo descompasso entre necessidade (carga de doença, "
    "déficit sanitário, vulnerabilidade) e alocação (R$/hab em saúde). "
    "Vermelho = necessidade não atendida.",
)

tema.nota(
    "<strong>Como ler.</strong> O <em>Farol</em> combina os dois eixos num "
    "semáforo. As demais camadas mostram um subíndice ou uma camada de gasto "
    "isolada, sempre como <strong>percentil</strong> — a posição do município no "
    "ranking dos 185 (50% = mediana estadual). Municípios <strong>sem dado</strong> "
    "na camada aparecem esmaecidos: é ausência de informação, não valor zero."
)

# ── Filtros ────────────────────────────────────────────────────────────
anos = dados.anos()
ano = st.sidebar.selectbox("Ano", anos, index=len(anos) - 1)
camada = st.sidebar.selectbox(
    "Camada",
    list(tema.CAMADAS),
    format_func=lambda k: tema.CAMADAS[k],
)
st.sidebar.caption(
    "O **Farol** combina os dois eixos. As demais camadas mostram um subíndice "
    "ou uma camada de gasto isolada, para entender de onde vem a cor."
)

df = dados.coropletico(ano, camada)

meso_opts = ["(todas)"] + sorted(df["mesorregiao"].dropna().unique())
meso = st.sidebar.selectbox("Mesorregião", meso_opts)
if meso != "(todas)":
    df = df[df["mesorregiao"] == meso]

categorico = camada == "farol"
e_dinheiro = camada in tema.CAMADA_UNIDADE

if not categorico:
    serie = df["valor"].dropna()
    vmin = float(serie.min()) if not serie.empty else 0.0
    vmax = float(serie.max()) if not serie.empty else 1.0


def _fmt(v: float) -> str:
    if e_dinheiro:
        return f"R$ {v:,.0f}/hab".replace(",", ".")
    return f"percentil {v:.0%}"


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


# ── Indicadores ────────────────────────────────────────────────────────
n_total = df["cod_ibge"].nunique()
if categorico:
    dist = df["valor"].value_counts()
    com_cor = int((df["valor"] != "cinza").sum())
    tema.cartoes(
        [
            (str(n_total), "municípios no recorte"),
            (str(com_cor), "com IEAS calculado"),
            (str(int(dist.get("vermelho", 0))), "no vermelho (necessidade não atendida)"),
            (str(int(dist.get("cinza", 0))), "cinza (cobertura de dados insuficiente)"),
        ]
    )
    if com_cor == 0:
        st.info(
            "**Tudo cinza neste recorte.** A regra do cinza só calcula o IEAS "
            "quando os dois eixos têm cobertura mínima. Troque o ano ou a camada.",
            icon="ℹ️",
        )
    elif n_total - com_cor > 0:
        st.caption(
            f"{n_total - com_cor} município(s) em cinza: a cobertura do eixo "
            "Alocação (L1 + L2 + L3) fica abaixo do limiar. O eixo Necessidade "
            "(epidemiologia + saneamento + vulnerabilidade) está completo para os "
            "185 municípios em todos os anos."
        )
else:
    com_dado = int(df["valor"].notna().sum())
    tema.cartoes(
        [
            (str(n_total), "municípios no recorte"),
            (str(com_dado), "com dado nesta camada"),
            (f"{com_dado / n_total:.0%}" if n_total else "—", "cobertura da camada"),
            (
                _fmt(float(df["valor"].median())) if com_dado else "—",
                "mediana estadual",
            ),
        ]
    )

# ── Mapa ───────────────────────────────────────────────────────────────
nome_por_cod = dados.ieas().drop_duplicates("cod_ibge").set_index("cod_ibge")["nome"].to_dict()
geojson = copy.deepcopy(dados.malhas_geojson())
for feat in geojson["features"]:
    cod = str(feat["id"])
    feat["properties"] = {
        "cod_ibge": cod,
        "nome": nome_por_cod.get(cod, cod),
        "valor": _rotulo_valor(cod),
    }

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
        aliases=["Município", tema.CAMADAS[camada].split("—")[0].split("·")[0].strip() + ":"],
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
    if categorico:
        st.caption(
            "Verde é o alvo (alinhamento), não o topo de uma escala. Azul é sobrealocação relativa."
        )

# ── Ranking + tabela (identidade nunca só por cor) ─────────────────────
rot_valor = tema.CAMADAS[camada].split("—")[0].split("·")[-1].strip()
tab = df[["cod_ibge", "nome", "mesorregiao", "valor"]].rename(
    columns={
        "cod_ibge": "Cód. IBGE",
        "nome": "Município",
        "mesorregiao": "Mesorregião",
        "valor": rot_valor,
    }
)
tab = tab.sort_values(rot_valor, ascending=categorico, na_position="last")

if not categorico:
    st.subheader("Extremos nesta camada")
    e1, e2 = st.columns(2)
    with e1:
        st.markdown(f"**Maiores** — {rot_valor}")
        st.dataframe(tab.head(8), width="stretch", hide_index=True)
    with e2:
        st.markdown(f"**Menores** — {rot_valor}")
        st.dataframe(tab.dropna(subset=[rot_valor]).tail(8)[::-1], width="stretch", hide_index=True)

with st.expander("Ver tabela completa"):
    st.dataframe(tab, width="stretch", hide_index=True)
    st.download_button(
        "Baixar CSV",
        tab.to_csv(index=False).encode("utf-8"),
        file_name=f"farol_{camada}_{ano}.csv",
        mime="text/csv",
    )

# ── Alertas do ano ─────────────────────────────────────────────────────
al = dados.alertas()
al = al[al["ano"] == ano] if not al.empty else al
if not al.empty:
    st.subheader(f"Alertas em {ano}")
    dim = dados.ieas().drop_duplicates("cod_ibge").set_index("cod_ibge")["nome"]
    al = al.assign(Município=al["cod_ibge"].map(dim))
    st.dataframe(
        al[["Município", "tipo", "severidade", "explicacao"]].rename(
            columns={"tipo": "Tipo", "severidade": "Severidade", "explicacao": "Explicação"}
        ),
        width="stretch",
        hide_index=True,
    )
    st.caption("Detalhe, filtros e a definição de cada detector na página **Alertas**.")

tema.rodape(
    "SINAN e SIH (epidemiologia), PNCP e Compras.gov.br (L3), SIOPS (L2), "
    "Portal da Transparência (L1), Censo 2022 (saneamento), CadÚnico "
    "(vulnerabilidade), IBGE (população, malha)."
)

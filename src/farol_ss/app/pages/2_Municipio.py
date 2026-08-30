"""Página Município — drill-down de um município ao longo do recorte.

Abre a caixa-preta do IEAS: os componentes presentes de cada eixo com seus
valores, a série de casos por agravo, a incidência por 100 mil, as três
camadas de gasto per capita, as contratações no PNCP e os alertas. Onde uma
camada não entra, a página diz explicitamente — a ausência é informação.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from farol_ss.app import dados, tema

st.set_page_config(page_title="Município · Farol-SS", page_icon="🔎", layout="wide")
tema.aplicar_estilo()

fato = dados.fato()
municipios = fato[["cod_ibge", "nome"]].drop_duplicates().sort_values("nome")

nome = st.sidebar.selectbox("Município", municipios["nome"].tolist())
cod = municipios.loc[municipios["nome"] == nome, "cod_ibge"].iloc[0]
m = fato[fato["cod_ibge"] == cod].sort_values("ano")
ultimo = m.iloc[-1]

tema.cabecalho(
    f"🔎 {nome}",
    f"Código IBGE {cod} · {ultimo['mesorregiao']} · recorte "
    f"{int(m['ano'].min())}–{int(m['ano'].max())}.",
    kicker="Perfil municipal",
)

tema.nota(
    "Esta página abre a caixa-preta do IEAS para um município: os componentes "
    "presentes de cada eixo, as séries de casos e de gasto, as contratações no "
    "PNCP e os alertas. <strong>Percentil</strong> é a posição no ranking dos 185 "
    "municípios de PE (100% = maior do estado). Onde uma camada não entra no "
    "cálculo, a página diz explicitamente."
)

pop_atual = int(ultimo["populacao"])
gap = ultimo["gap"]
tema.cartoes(
    [
        (f"{pop_atual:,}".replace(",", "."), f"habitantes ({int(ultimo['ano'])})"),
        (tema.FAROL_ROTULO[ultimo["farol"]], f"farol em {int(ultimo['ano'])}"),
        (f"{gap:+.2f}" if pd.notna(gap) else "—", "gap = rank(A) − rank(N)"),
        (
            f"{ultimo['necessidade_rank']:.0%}" if pd.notna(ultimo["necessidade_rank"]) else "—",
            "percentil de necessidade no estado",
        ),
        (
            f"{ultimo['alocacao_rank']:.0%}" if pd.notna(ultimo["alocacao_rank"]) else "—",
            "percentil de alocação no estado",
        ),
    ]
)

# ── Eixo Necessidade ──────────────────────────────────────────────────
st.header("Eixo Necessidade")
comp_n = [
    (
        "Carga epidemiológica",
        "sub_epidemiologico",
        "SINAN (arboviroses + veiculação hídrica) + internações DRSAI (SIH)",
    ),
    (
        "Déficit de saneamento",
        "sub_saneamento",
        f"Censo {int(ultimo.get('saneamento_ano_referencia', 2022))} — água + esgoto + lixo",
    ),
    ("Vulnerabilidade social", "sub_vulnerabilidade", "CadÚnico — famílias em extrema pobreza"),
]
cols = st.columns(3)
for (rot, col, fonte), c in zip(comp_n, cols):
    val = ultimo.get(col)
    c.metric(rot, f"percentil {val:.0%}" if pd.notna(val) else "sem dado")
    c.caption(fonte)
st.caption(
    f"Cobertura do eixo: **{ultimo['necessidade_cobertura']:.0%}** "
    "(o IEAS exige ≥ 60%). O rank percentil é calculado entre os 185 municípios."
)

# ── Eixo Alocação ─────────────────────────────────────────────────────
st.header("Eixo Alocação — R$/hab deflacionado para 2024")
comp_a = [
    (
        "L1 · repasse federal",
        "l1_per_capita",
        "Portal da Transparência (proxy: transferências sociais)",
    ),
    ("L2 · execução própria", "l2_per_capita", "SIOPS — despesa com recursos próprios em saúde"),
    ("L3 · contratação de insumos", "l3_per_capita", "PNCP (municipal) + Compras.gov.br (federal)"),
]
cols = st.columns(3)
for (rot, col, fonte), c in zip(comp_a, cols):
    val = ultimo.get(col)
    c.metric(rot, f"R$ {val:,.0f}".replace(",", ".") if pd.notna(val) else "sem dado")
    c.caption(fonte)
st.caption(
    f"Cobertura do eixo: **{ultimo['alocacao_cobertura']:.0%}** (o IEAS exige ≥ 50%). "
    "L1 está completo para os 185 municípios; onde falta L2 ou L3, o município não "
    "publicou execução própria no SIOPS ou não teve contratação no PNCP naquele ano."
)

serie_a = m.set_index("ano")[["l1_per_capita", "l2_per_capita", "l3_per_capita"]].rename(
    columns={
        "l1_per_capita": "L1 repasse",
        "l2_per_capita": "L2 próprio",
        "l3_per_capita": "L3 insumos",
    }
)
if serie_a.notna().any().any():
    st.line_chart(serie_a)

# ── Epidemiologia ─────────────────────────────────────────────────────
st.header("Carga de doença")
epi = dados.epidemiologia()
epi_m = epi[epi["cod_ibge"] == cod].copy()
c1, c2 = st.columns(2)
with c1:
    st.subheader("Notificações por agravo (SINAN)")
    if not epi_m.empty:
        epi_m["agravo"] = epi_m["agravo"].map(lambda a: tema.AGRAVOS.get(a.lower(), a))
        pivot = epi_m.pivot_table(index="ano", columns="agravo", values="casos", aggfunc="sum")
        st.bar_chart(pivot)
    else:
        st.info("Sem notificações registradas no recorte.")
with c2:
    st.subheader("Internações DRSAI (SIH)")
    if "internacoes_drsai" in m.columns and m["internacoes_drsai"].notna().any():
        st.bar_chart(m.set_index("ano")["internacoes_drsai"].rename("internações"))
        st.caption(
            "Internações por doença relacionada a saneamento ambiental inadequado — "
            "diarreias, hepatite A, leptospirose, esquistossomose, helmintíases."
        )
    else:
        st.info("Sem internações DRSAI registradas.")

taxa_cols = [c for c in m.columns if c.startswith("taxa_") and c != "taxa_internacoes_drsai"]
if taxa_cols:
    st.subheader("Incidência por 100 mil habitantes")
    taxas = m.set_index("ano")[taxa_cols].rename(
        columns=lambda c: tema.AGRAVOS.get(c.replace("taxa_", ""), c)
    )
    st.line_chart(taxas)

# ── Contratações no PNCP ──────────────────────────────────────────────
pncp = dados.pncp()
if not pncp.empty:
    compras_m = pncp[pncp["cod_ibge"] == cod].sort_values("data_publicacao_pncp", ascending=False)
    if not compras_m.empty:
        st.header(f"Contratações no PNCP ({len(compras_m)})")
        st.dataframe(
            compras_m[["ano", "modalidade_nome", "objeto_compra", "valor_total_homologado"]].rename(
                columns={
                    "ano": "Ano",
                    "modalidade_nome": "Modalidade",
                    "objeto_compra": "Objeto",
                    "valor_total_homologado": "Valor homologado (R$)",
                }
            ),
            width="stretch",
            hide_index=True,
        )

# ── Alertas ───────────────────────────────────────────────────────────
al = dados.alertas()
al_m = al[al["cod_ibge"] == cod] if not al.empty else al
if not al_m.empty:
    st.header("Alertas")
    st.dataframe(
        al_m[["ano", "tipo", "severidade", "explicacao"]].rename(
            columns={
                "ano": "Ano",
                "tipo": "Tipo",
                "severidade": "Severidade",
                "explicacao": "Explicação",
            }
        ),
        width="stretch",
        hide_index=True,
    )

tema.rodape(
    "SINAN e SIH (DATASUS), PNCP e Compras.gov.br, SIOPS, Portal da Transparência, "
    "Censo 2022 do IBGE, CadÚnico/SAGI, IBGE (população, IPCA)."
)

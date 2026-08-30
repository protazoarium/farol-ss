"""Página Alertas — a tabela de anomalias explicáveis.

Cada linha é um alerta com `explicacao` em linguagem natural: um alerta que
um cidadão não consegue ler não serve para controle social. Os quatro
detectores do plano estão ativos — a definição de cada um fica em
`conteudo.DETECTORES`.
"""

from __future__ import annotations

import streamlit as st

from farol_ss.app import conteudo, dados, tema

st.set_page_config(page_title="Alertas · Farol-SS", page_icon="🔔", layout="wide")
tema.aplicar_estilo()

tema.cabecalho(
    "🔔 Alertas explicáveis",
    "Quatro detectores varrem o cruzamento de necessidade, gasto e contratação. "
    "Cada alerta traz uma explicação legível e é uma suspeita para auditoria, "
    "não uma conclusão.",
)

tema.nota(
    "<strong>Severidade</strong> (alta / moderada) vem da intensidade do desvio, "
    "não da gravidade sanitária. Use os filtros para recortar por tipo, ano e "
    "mesorregião; baixe o CSV para levar a suspeita adiante. A fórmula de cada "
    "detector está na página <strong>Metodologia</strong>."
)

al = dados.alertas()
if al.empty:
    st.info("Nenhum alerta gerado. Rode `farol ieas` para (re)calcular.", icon="ℹ️")
    st.stop()

dim = dados.ieas().drop_duplicates("cod_ibge").set_index("cod_ibge")
al = al.assign(
    município=al["cod_ibge"].map(dim["nome"]),
    mesorregião=al["cod_ibge"].map(dim["mesorregiao"]),
)

por_tipo = al["tipo"].value_counts()
tema.cartoes([(str(int(por_tipo.get(chave, 0))), rot) for rot, chave, _ in conteudo.DETECTORES])

# ── Filtros ────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
tipos = c1.multiselect("Tipo", sorted(al["tipo"].unique()), default=list(al["tipo"].unique()))
anos_sel = c2.multiselect("Ano", sorted(al["ano"].unique()), default=sorted(al["ano"].unique()))
mesos = c3.multiselect("Mesorregião", sorted(al["mesorregião"].dropna().unique()))

f = al[al["tipo"].isin(tipos) & al["ano"].isin(anos_sel)]
if mesos:
    f = f[f["mesorregião"].isin(mesos)]

k1, k2, k3 = st.columns(3)
k1.metric("Alertas no filtro", len(f))
k2.metric("Municípios distintos", f["cod_ibge"].nunique())
k3.metric("Anos cobertos", f["ano"].nunique())

if not f.empty:
    st.bar_chart(f.groupby("ano").size().rename("alertas"))

st.dataframe(
    f[["ano", "município", "mesorregião", "tipo", "severidade", "explicacao"]]
    .sort_values(["ano", "município"])
    .rename(
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

st.download_button(
    "Baixar CSV",
    f.to_csv(index=False).encode("utf-8"),
    file_name="alertas_farol_ss.csv",
    mime="text/csv",
)

# ── O que cada detector faz ───────────────────────────────────────────
st.header("Os quatro detectores")
for rot, chave, desc in conteudo.DETECTORES:
    with st.container(border=True):
        st.markdown(f"#### {rot}")
        st.caption(f"`{chave}` · {int(por_tipo.get(chave, 0))} alertas no recorte")
        st.markdown(desc)

st.warning(conteudo.LIMITACAO_ALERTAS, icon="⚠️")

tema.rodape(
    "SINAN (incidência), PNCP e Compras.gov.br (contratações e itens), o IEAS (faróis vermelhos)."
)

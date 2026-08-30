"""Página Alertas — a tabela de anomalias explicáveis.

Cada linha é um alerta com `explicacao` em linguagem natural: um alerta que
um cidadão não consegue ler não serve para controle social. Dois detectores
ativos nesta versão (ver Metodologia para por que 2 e 3 estão fora):

- **desalinhamento_estrutural** — farol vermelho: necessidade alta, alocação
  baixa. Depende do IEAS ter cor, então hoje não produz linhas.
- **suspeita_desabastecimento** — incidência de um agravo no topo da
  distribuição de PE num ano, com o município publicando compras no PNCP
  naquele ano mas nenhuma da categoria de insumo esperada.
"""

from __future__ import annotations

import streamlit as st

from farol_ss.app import dados

st.set_page_config(page_title="Alertas · Farol-SS", page_icon="🔔", layout="wide")

st.title("🔔 Alertas")

al = dados.alertas()
if al.empty:
    st.info(
        "Nenhum alerta gerado. Rode `farol ieas` para (re)calcular. O detector "
        "de desalinhamento estrutural só dispara quando o IEAS tem cor — "
        "pendente das fontes de Alocação."
    )
    st.stop()

dim = dados.ieas().drop_duplicates("cod_ibge").set_index("cod_ibge")
al = al.assign(
    município=al["cod_ibge"].map(dim["nome"]),
    mesorregião=al["cod_ibge"].map(dim["mesorregiao"]),
)

c1, c2, c3 = st.columns(3)
tipos = c1.multiselect("Tipo", sorted(al["tipo"].unique()), default=list(al["tipo"].unique()))
anos_sel = c2.multiselect("Ano", sorted(al["ano"].unique()), default=sorted(al["ano"].unique()))
mesos = c3.multiselect("Mesorregião", sorted(al["mesorregião"].dropna().unique()))

f = al[al["tipo"].isin(tipos) & al["ano"].isin(anos_sel)]
if mesos:
    f = f[f["mesorregião"].isin(mesos)]

k1, k2, k3 = st.columns(3)
k1.metric("Alertas", len(f))
k2.metric("Municípios distintos", f["cod_ibge"].nunique())
k3.metric("Anos cobertos", f["ano"].nunique())

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

st.caption(
    "Limitação conhecida: o casamento compra × insumo é por palavra-chave sobre "
    "o objeto da licitação (`seeds/catmat_saude.csv`), não NLP — pode gerar "
    "falso-positivo quando o insumo foi comprado sob descrição atípica. O alerta "
    "é uma *suspeita* para auditoria, não uma conclusão."
)

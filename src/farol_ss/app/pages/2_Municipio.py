"""Página Município — drill-down de um município ao longo do recorte.

Abre a caixa-preta do IEAS para um município: quais componentes de cada eixo
existem, a série de casos por agravo, o gasto L3 per capita e os alertas.
Enquanto L1/L2/saneamento/vulnerabilidade não entram, a página mostra
explicitamente o que falta — a ausência é informação.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from farol_ss.app import dados, tema

st.set_page_config(page_title="Município · Farol-SS", page_icon="🔎", layout="wide")

ieas = dados.ieas()
municipios = ieas[["cod_ibge", "nome"]].drop_duplicates().sort_values("nome")

nome = st.sidebar.selectbox("Município", municipios["nome"].tolist())
cod = municipios.loc[municipios["nome"] == nome, "cod_ibge"].iloc[0]

m = ieas[ieas["cod_ibge"] == cod].sort_values("ano")

st.title(f"🔎 {nome}")
meso = m["mesorregiao"].iloc[0]
st.caption(f"{cod} · {meso} · recorte {int(m['ano'].min())}–{int(m['ano'].max())}")

pop_atual = int(m.iloc[-1]["populacao"])
k1, k2, k3 = st.columns(3)
k1.metric("População (último ano)", f"{pop_atual:,}".replace(",", "."))
k2.metric("Farol (último ano)", tema.FAROL_ROTULO[m.iloc[-1]["farol"]])
l3_medio = m["l3_per_capita"].mean(skipna=True)
k3.metric("L3 médio (R$/hab)", "—" if pd.isna(l3_medio) else f"{l3_medio:,.2f}".replace(",", "."))

# --- Eixo Necessidade: o que existe, o que falta ---------------------
st.subheader("Eixo Necessidade — componentes")
comp_n = {
    "Epidemiológico (SINAN)": m["sub_epidemiologico"].notna().any(),
    "Saneamento (SNIS)": m["sub_saneamento"].notna().any(),
    "Vulnerabilidade (CadÚnico)": m["sub_vulnerabilidade"].notna().any(),
}
cols = st.columns(3)
for (rot, ok), c in zip(comp_n.items(), cols):
    c.markdown(f"{'✅' if ok else '⬜'} {rot}")
st.caption(
    "O IEAS só é calculado quando ≥ 60% dos componentes de Necessidade existem "
    f"(`conf/ieas.yml`). Hoje: {sum(comp_n.values())}/3."
)

# --- Casos por agravo ao longo do tempo -----------------------------
st.subheader("Notificações por agravo (SINAN)")
epi = dados.epidemiologia()
epi_m = epi[epi["cod_ibge"] == cod].copy()
if not epi_m.empty:
    epi_m["agravo"] = epi_m["agravo"].map(lambda a: tema.AGRAVOS.get(a.lower(), a))
    pivot = epi_m.pivot_table(index="ano", columns="agravo", values="casos", aggfunc="sum")
    st.bar_chart(pivot)
    with st.expander("Tabela de casos"):
        st.dataframe(pivot.fillna(0).astype(int), width="stretch")
else:
    st.info("Sem notificações registradas para este município no recorte.")

# --- Taxas por 100 mil hab. -----------------------------------------
taxa_cols = [c for c in m.columns if c.startswith("taxa_")]
if taxa_cols:
    st.subheader("Incidência por 100 mil habitantes")
    taxas = m.set_index("ano")[taxa_cols].rename(
        columns=lambda c: tema.AGRAVOS.get(c.replace("taxa_", ""), c)
    )
    st.line_chart(taxas)

# --- Eixo Alocação: L3 (PNCP) --------------------------------------
st.subheader("Eixo Alocação — contratação de insumos L3 (PNCP)")
if m["l3_per_capita"].notna().any():
    st.line_chart(m.set_index("ano")[["l3_total", "l3_per_capita"]])
else:
    st.info("Nenhuma contratação deste município encontrada no PNCP no recorte.")
st.caption("L1 (repasse federal) e L2 (execução própria) ainda não ingeridos — ver Metodologia.")

pncp = dados.pncp()
if not pncp.empty:
    compras_m = pncp[pncp["cod_ibge"] == cod].sort_values("data_publicacao_pncp", ascending=False)
    if not compras_m.empty:
        with st.expander(f"Contratações no PNCP ({len(compras_m)})"):
            st.dataframe(
                compras_m[
                    ["ano", "modalidade_nome", "objeto_compra", "valor_total_homologado"]
                ].rename(
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

# --- Alertas do município -----------------------------------------
al = dados.alertas()
al_m = al[al["cod_ibge"] == cod] if not al.empty else al
if not al_m.empty:
    st.subheader("Alertas")
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

"""Ponto de entrada do painel Farol-SS (`make app`).

Página de rosto: o que o índice mede, o estado real das fontes e por que o
farol ainda está cinza. As páginas de análise ficam em `pages/`.
"""

from __future__ import annotations

import streamlit as st

from farol_ss.app import dados

st.set_page_config(page_title="Farol da Saúde & Saneamento", page_icon="🚦", layout="wide")

st.title("🚦 Farol da Saúde & Saneamento")
st.markdown(
    "Monitor territorial de **efetividade do gasto em saúde** nos 185 municípios "
    "de Pernambuco. Cruza execução financeira com carga epidemiológica, déficit "
    "sanitário e vulnerabilidade social e produz o **IEAS — Índice de "
    "Efetividade da Alocação Sanitária**."
)

st.subheader("Como ler o índice")
st.markdown(
    """
Dois eixos, cada um um **rank percentil dentro de PE**:

- **N — Necessidade**: epidemiologia (SINAN) + saneamento (SNIS) + vulnerabilidade (CadÚnico)
- **A — Alocação**: R$/hab deflacionado — repasse federal (L1) + execução própria (L2) + compras de insumos (L3)

`gap = rank(A) − rank(N)` ∈ [−1, 1] colore o farol. `ieas = 1 − |gap|` serve só para ranquear.

Um eixo sem cobertura mínima (`conf/ieas.yml`) **não** tem IEAS calculado — o
farol mostra cinza, nunca um número sobre dado majoritariamente ausente.
"""
)

st.subheader("Estado das fontes")
st.markdown(
    """
| Fonte | Eixo | Estado |
|---|---|---|
| IBGE (população, IPCA, malha) | base | ✅ ingerido |
| SINAN — 6 agravos × 5 anos | N · epidemiologia | ✅ ingerido |
| PNCP — compras municipais | A · L3 | ✅ parcial (ingestão em curso) |
| Portal da Transparência | A · L1 | 🔴 HTTP 403 |
| SIOPS | A · L2 | 🔴 sem API real |
| SNIS | N · saneamento | 🔴 DNS fora do ar |
| CadÚnico | N · vulnerabilidade | ⏳ não iniciado |

Enquanto L1, L2 e saneamento não entram, o eixo de Alocação fica em 33% de
cobertura (mínimo 50%) e o de Necessidade em 33% (mínimo 60%) — por isso o
**farol está todo cinza**. É a regra do cinza funcionando, não um bug: o
pipeline inteiro (ingestão → gold → IEAS → alertas) já roda e passa a colorir
sozinho quando as fontes destravarem.
"""
)

try:
    df = dados.ieas()
    ano_max = int(df["ano"].max())
    c1, c2, c3 = st.columns(3)
    c1.metric("Municípios", df["cod_ibge"].nunique())
    c2.metric("Município-anos no gold", len(df))
    c3.metric("Farol com cor", int((df["farol"] != "cinza").sum()))
    st.caption(f"Gold carregado — recorte {int(df['ano'].min())}–{ano_max}.")
except FileNotFoundError:
    st.warning("Gold ainda não gerado. Rode `make all` (ou `farol gold && farol ieas`).")

st.page_link("pages/1_Farol.py", label="Abrir o mapa do Farol", icon="🚦")

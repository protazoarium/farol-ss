"""Página Metodologia — a fórmula do IEAS e a proveniência dos dados.

Tudo aqui é lido de `conf/ieas.yml` e de `data/manifest.json` em tempo de
execução: a página não repete número nenhum que já vive na configuração, e
a tabela de proveniência reflete a última coleta de fato.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from farol_ss.app import dados
from farol_ss.config import ieas_conf

st.set_page_config(page_title="Metodologia · Farol-SS", page_icon="📐", layout="wide")
conf = ieas_conf()

st.title("📐 Metodologia")

st.markdown(
    """
O **IEAS — Índice de Efetividade da Alocação Sanitária** compara, dentro de
Pernambuco, o quanto um município **precisa** com o quanto ele **recebe/gasta**
em saúde. Não é um índice de qualidade de gestão nem de execução orçamentária:
é um índice de **alinhamento territorial** entre necessidade e alocação.
"""
)

st.header("Os dois eixos")
st.markdown(
    """
Cada eixo é um **rank percentil** ∈ [0, 1] calculado entre os 185 municípios —
o valor absoluto (R$, taxa por 100 mil) não entra na conta final, só a posição
relativa. Isso torna o índice robusto a inflação, a mudança de escala das
fontes e a *outliers*.
"""
)

col_n, col_a = st.columns(2)
with col_n:
    st.subheader("N — Necessidade")
    pn = conf["necessidade"]["pesos"]
    st.table(
        pd.DataFrame(
            {
                "componente": [
                    "Epidemiológico (SINAN)",
                    "Saneamento (SNIS)",
                    "Vulnerabilidade (CadÚnico)",
                ],
                "peso": [pn["epidemiologico"], pn["saneamento"], pn["vulnerabilidade"]],
                "status": ["✅ ingerido", "🔴 SNIS fora do ar", "⏳ não iniciado"],
            }
        )
    )
    ep = conf["necessidade"]["epidemiologico"]["pesos"]
    st.caption(
        f"Subíndice epidemiológico hoje: arboviroses {ep['arboviroses']:.0%} "
        f"(dengue+chik+zika) + veiculação hídrica {ep['veiculacao_hidrica']:.0%} "
        "(lept+hepA+esquisto). O peso de internações (SIH) foi redistribuído — "
        "nenhum grupo utilizável do SIH nesta versão do PySUS."
    )
with col_a:
    st.subheader("A — Alocação")
    pa = conf["alocacao"]["pesos"]
    st.table(
        pd.DataFrame(
            {
                "camada": [
                    "L1 — repasse federal",
                    "L2 — execução própria",
                    "L3 — contratação de insumos",
                ],
                "fonte": ["Portal da Transparência", "SIOPS", "PNCP + Compras.gov.br"],
                "peso": [
                    pa["l1_repasse_federal"],
                    pa["l2_execucao_propria"],
                    pa["l3_contratacao_insumos"],
                ],
                "status": ["🔴 HTTP 403", "🔴 sem API", "✅ PNCP ingerido (parcial)"],
            }
        )
    )
    st.caption(
        f"Valores per capita deflacionados para {conf['recorte']['ano_base_deflacao']} pelo IPCA."
    )

st.header("Do eixo ao farol")
farol = conf["farol"]
st.markdown(
    f"""
- **gap = rank(A) − rank(N)** ∈ [−1, 1]
- **ieas = 1 − |gap|** ∈ [0, 1] — usado apenas para ranquear, nunca para colorir

| Faixa de gap | Farol | Leitura |
|---|---|---|
| gap ≤ {farol["vermelho_ate"]} | 🔴 vermelho | necessidade muito acima da alocação |
| {farol["vermelho_ate"]} < gap ≤ {farol["amarelo_ate"]} | 🟠 amarelo | subalocação leve |
| \\|gap\\| ≤ {farol["verde_ate"]} | 🟢 verde | alinhado |
| gap ≥ {farol["azul_a_partir"]} | 🔵 azul | alocação acima da necessidade |
"""
)

cm = conf["cobertura_minima"]
st.subheader("Regra do cinza")
st.markdown(
    f"""
Um eixo cuja fração de componentes presentes cai abaixo do limiar **não tem
IEAS calculado** — o farol fica cinza. Limiares: Necessidade **{cm["necessidade"]:.0%}**,
Alocação **{cm["alocacao"]:.0%}**. Hoje os dois eixos estão em ~33% de cobertura,
então **todo o mapa está cinza** — é a regra funcionando, não um defeito. As
cores aparecem sozinhas quando Transparência (L1), SIOPS (L2) e SNIS
(saneamento) forem ingeridos.
"""
)

st.header("Correção metodológica sobre a proposta original")
st.markdown(
    """
A proposta assumia ver "compras de medicamentos por município" no
Compras.gov.br. Esse portal registra compras de **órgãos federais** (por UASG),
não de prefeituras. O eixo financeiro foi então decomposto em três camadas
genuinamente municipalizáveis (L1/L2/L3 acima), sendo o **PNCP** — onde as
prefeituras publicam sob a Lei 14.133/2021 — a fonte que viabiliza a análise
por município. Compras.gov.br entra como complemento federal, documentado como
limitação de escopo.
"""
)

st.header("Proveniência dos dados")
f = dados.fontes()
st.dataframe(
    f[["nome", "camada", "licenca", "coletado", "linhas", "coletado_em", "dados_gov"]].rename(
        columns={
            "nome": "Fonte",
            "camada": "Camada",
            "licenca": "Licença",
            "coletado": "Coletado",
            "linhas": "Linhas",
            "coletado_em": "Última coleta",
            "dados_gov": "Conjunto no dados.gov.br",
        }
    ),
    width="stretch",
    hide_index=True,
    column_config={"Conjunto no dados.gov.br": st.column_config.LinkColumn()},
)
st.caption(
    "Requisito do Concurso de Reúso de Dados Abertos da CGU: ao menos um "
    "conjunto catalogado no dados.gov.br. O projeto usa quatro (IBGE, SINAN, "
    "PNCP e o Portal da Transparência da própria CGU)."
)

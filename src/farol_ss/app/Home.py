"""Ponto de entrada do painel Farol-SS (`make app`).

Página de rosto institucional: o que o índice mede, para quem, como se lê, o
diagrama de construção, o estado real das oito fontes e os atalhos para as
páginas de análise.
"""

from __future__ import annotations

import streamlit as st

from farol_ss.app import conteudo, dados, tema
from farol_ss.config import ieas_conf

st.set_page_config(
    page_title=f"{tema.MARCA}",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)
tema.aplicar_estilo()
conf = ieas_conf()

tema.cabecalho(
    f"🚦 {tema.MARCA}",
    tema.DESCRICAO_CURTA + " — pipeline de dados abertos, painel e API aberta.",
    kicker="Monitor territorial de efetividade da alocação sanitária",
)

# ── Números do recorte ────────────────────────────────────────────────
try:
    df = dados.ieas()
    ano_min, ano_max = int(df["ano"].min()), int(df["ano"].max())
    com_cor = int((df["farol"] != "cinza").sum())
    alertas = dados.alertas()
    tema.cartoes(
        [
            ("185", "municípios de Pernambuco"),
            (f"{ano_min}–{ano_max}", "recorte temporal"),
            ("8", "fontes federais abertas"),
            (f"{com_cor}", "município-anos com IEAS calculado"),
            (f"{len(alertas)}" if not alertas.empty else "—", "alertas explicáveis emitidos"),
        ]
    )
except FileNotFoundError:
    st.warning("Camada gold ainda não gerada. Rode `make all` (ou `farol gold && farol ieas`).")
    st.stop()

# ── O que é ───────────────────────────────────────────────────────────
st.header("O que este painel mede")
st.markdown(conteudo.O_QUE_E)

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Para quem")
    st.markdown(conteudo.PARA_QUEM)
with col_b:
    st.subheader("Os dois eixos do IEAS")
    st.markdown(
        f"""
Cada eixo é convertido num **rank percentil dentro de Pernambuco** (posição
relativa, não valor absoluto):

- **N — Necessidade**: carga epidemiológica (SINAN + internações SIH,
  {conf['necessidade']['pesos']['epidemiologico']:.0%}) + déficit de saneamento
  (Censo 2022, {conf['necessidade']['pesos']['saneamento']:.0%}) + vulnerabilidade
  social (CadÚnico, {conf['necessidade']['pesos']['vulnerabilidade']:.0%}).
- **A — Alocação**: R$/hab deflacionado para 2024 — repasse federal L1
  ({conf['alocacao']['pesos']['l1_repasse_federal']:.0%}) + execução própria L2
  ({conf['alocacao']['pesos']['l2_execucao_propria']:.0%}) + contratação de
  insumos L3 ({conf['alocacao']['pesos']['l3_contratacao_insumos']:.0%}).

A fórmula completa, com cada subíndice e cada detector, está na página
**Metodologia**.
"""
    )

st.markdown("### Como ler o índice")
st.markdown(conteudo.COMO_LER)

# ── Diagrama ─────────────────────────────────────────────────────────
st.markdown("### Como o índice é construído")
tema.diagrama_indice(conf["necessidade"]["pesos"], conf["alocacao"]["pesos"])

# ── Semáforo ──────────────────────────────────────────────────────────
st.markdown("### O semáforo")
st.markdown(
    "O sinal do `gap` escolhe a cor. **Verde é o alvo** — alinhamento entre "
    "necessidade e alocação — não o topo de uma escala; azul é sobrealocação "
    "relativa; cinza é ausência de dado, nunca um resultado."
)
for cor in tema.FAROL_ORDEM:
    st.markdown(
        f'<div style="display:flex;gap:.7rem;align-items:baseline;margin:.4rem 0">'
        f'<span class="fss-pill" style="background:{tema.FAROL_COR[cor]};color:#fff">'
        f"{tema.FAROL_ROTULO[cor]}</span>"
        f'<span style="font-size:.9rem;color:{tema.TINTA_2}">{tema.FAROL_LEITURA[cor]}</span></div>',
        unsafe_allow_html=True,
    )

# ── Estado das fontes ─────────────────────────────────────────────────
st.header("As oito fontes")
st.caption(
    "Todas federais e abertas, catalogadas no Portal Brasileiro de Dados Abertos "
    "(dados.gov.br). Papel no índice, cobertura real e limitações na página **Fontes**."
)
resumo = dados.resumo_fontes()
for f in conteudo.FONTES:
    if f.eixo == "Base":
        continue
    r = resumo.get(f.chave, {})
    coletado = r.get("coletado_em") or ""
    quando = f" · última coleta {coletado[:10]}" if coletado else ""
    st.markdown(
        f'<span class="fss-pill {conteudo.PILL_CLASS[f.estado]}">'
        f"{conteudo.PILL_LABEL[f.estado]}</span> &nbsp; "
        f"**{f.nome}** — <span style='color:{tema.TINTA_3};font-size:.85rem'>"
        f"{f.orgao}{quando}</span>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div style='font-size:.88rem;color:{tema.TINTA_2};margin:.1rem 0 .8rem 0'>"
        f"{f.eixo} — {f.transformacao or f.papel}</div>",
        unsafe_allow_html=True,
    )

# ── Navegação ─────────────────────────────────────────────────────────
st.header("Navegar")
n1, n2, n3 = st.columns(3)
n1.page_link("pages/1_Farol.py", label="Farol — o mapa", icon="🚦")
n1.page_link("pages/2_Municipio.py", label="Município — drill-down", icon="🔎")
n2.page_link("pages/3_Alertas.py", label="Alertas explicáveis", icon="🔔")
n2.page_link("pages/4_Fontes.py", label="Fontes de dados", icon="🗂️")
n3.page_link("pages/5_Metodologia.py", label="Metodologia", icon="📐")
n3.page_link("pages/6_API.py", label="API aberta", icon="🔌")

tema.rodape()

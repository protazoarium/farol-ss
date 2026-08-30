"""Página Metodologia — todas as fontes e todas as fórmulas do IEAS.

Nenhum número mágico: pesos, limiares e ano-base vêm de `conf/ieas.yml` e são
interpolados aqui em runtime, para o texto nunca divergir do cálculo. As
fórmulas (LaTeX) vivem em `conteudo.FORMULAS`. A tabela de proveniência
reflete a última coleta de fato (`data/manifest.json`).
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from farol_ss.app import conteudo, dados, tema
from farol_ss.config import ieas_conf

st.set_page_config(page_title="Metodologia · Farol-SS", page_icon="📐", layout="wide")
tema.aplicar_estilo()
conf = ieas_conf()
pn = conf["necessidade"]["pesos"]
pe = conf["necessidade"]["epidemiologico"]["pesos"]
ps = conf["necessidade"]["saneamento"]["pesos"]
pa = conf["alocacao"]["pesos"]
farol = conf["farol"]
cm = conf["cobertura_minima"]
ano_base = conf["recorte"]["ano_base_deflacao"]


def _pct(x: float) -> str:
    return f"{x:.0%}"


tema.cabecalho(
    "📐 Metodologia do IEAS",
    "Como oito fontes federais viram um semáforo por município. Toda fórmula, "
    "todo peso e todo limiar estão nesta página, com os valores que o pipeline "
    "usa de fato — lidos de `conf/ieas.yml`.",
)

# ── 1. O que mede ─────────────────────────────────────────────────────
st.header("O que o IEAS mede — e o que não mede")
st.markdown(
    """
O **IEAS — Índice de Efetividade da Alocação Sanitária** mede **alinhamento
territorial**: a distância entre a posição de um município no *ranking estadual
de necessidade* e a sua posição no *ranking estadual de alocação*. É uma medida
relativa, dentro de Pernambuco, para um dado ano.

Ele **não** mede qualidade da gestão, execução orçamentária, desperdício, nem
desfecho clínico. Um município no verde não "vai bem em saúde" — apenas recebe e
gasta em proporção parecida com o quanto precisa, comparado aos vizinhos.
"""
)

# ── 2. Diagrama ──────────────────────────────────────────────────────
tema.diagrama_indice(pn, pa)

# ── 3. Da fonte ao indicador ─────────────────────────────────────────
st.header("Da fonte ao indicador")
st.markdown(
    "Cada fonte federal passa por uma transformação explícita até virar uma "
    "coluna do fato município × ano. A ingestão é idempotente e registra "
    "proveniência (URL, SHA-256, contagem de linhas, data) em `data/manifest.json`."
)
for f in conteudo.FONTES:
    with st.container(border=True):
        st.markdown(
            f'#### {f.nome} '
            f'<span class="fss-pill {conteudo.PILL_CLASS[f.estado]}">'
            f"{conteudo.PILL_LABEL[f.estado]}</span>",
            unsafe_allow_html=True,
        )
        st.caption(f"{f.orgao} · {f.eixo}")
        if f.variavel_bruta:
            st.markdown(f"**Variável bruta.** {f.variavel_bruta}")
        if f.transformacao:
            st.markdown(f"**Transformação.** {f.transformacao}")
        if f.limitacao and f.limitacao != "—":
            st.markdown(f"**Limitação.** {f.limitacao}")

# ── 4. Métricas comuns ───────────────────────────────────────────────
st.header("As duas métricas comuns")
st.markdown(
    "Todo indicador do IEAS passa por estas duas operações. São elas que tornam "
    "o índice comparável entre fontes de escalas muito diferentes (R$, taxa por "
    "100 mil, fração de domicílios)."
)
for fx in conteudo.formulas_do_bloco("comuns"):
    tema.formula(fx.titulo, fx.latex, fx.glossa)

# ── 5. Eixo Necessidade ──────────────────────────────────────────────
st.header("Eixo N — Necessidade")
st.markdown(
    f"Média ponderada de três subíndices, cada um um rank percentil em [0, 1]. "
    f"Pesos de `conf/ieas.yml`: epidemiológico **{_pct(pn['epidemiologico'])}**, "
    f"saneamento **{_pct(pn['saneamento'])}**, vulnerabilidade **{_pct(pn['vulnerabilidade'])}**."
)
st.table(
    pd.DataFrame(
        {
            "Subíndice": [
                "Epidemiológico (SINAN + SIH)",
                "Saneamento (Censo 2022)",
                "Vulnerabilidade (CadÚnico)",
            ],
            "Peso no eixo N": [
                _pct(pn["epidemiologico"]),
                _pct(pn["saneamento"]),
                _pct(pn["vulnerabilidade"]),
            ],
        }
    )
)
for fx in conteudo.formulas_do_bloco("necessidade"):
    tema.formula(fx.titulo, fx.latex, fx.glossa)
    if fx.chave == "sub_epidemiologico":
        st.caption(
            f"Pesos internos: arboviroses **{_pct(pe['arboviroses'])}**, veiculação "
            f"hídrica **{_pct(pe['veiculacao_hidrica'])}**, internações DRSAI "
            f"**{_pct(pe['internacoes_saneamento'])}**."
        )
    if fx.chave == "sub_saneamento":
        st.caption(
            f"Pesos dos déficits (aplicados na ingestão): água "
            f"**{_pct(ps['deficit_agua'])}**, esgoto **{_pct(ps['deficit_esgoto'])}**, "
            f"lixo **{_pct(ps['deficit_residuos'])}**."
        )

# ── 6. Eixo Alocação ─────────────────────────────────────────────────
st.header("Eixo A — Alocação")
st.markdown(
    f"Média ponderada de três camadas de gasto per capita, deflacionadas para "
    f"**{ano_base}** pelo IPCA. Pesos: L1 repasse federal "
    f"**{_pct(pa['l1_repasse_federal'])}**, L2 execução própria "
    f"**{_pct(pa['l2_execucao_propria'])}**, L3 contratação de insumos "
    f"**{_pct(pa['l3_contratacao_insumos'])}**."
)
st.table(
    pd.DataFrame(
        {
            "Camada": ["L1 — repasse federal", "L2 — execução própria", "L3 — contratação de insumos"],
            "Fonte": [
                "Portal da Transparência (proxy social)",
                "SIOPS",
                "PNCP (municipal) + Compras.gov.br (federal)",
            ],
            "Peso no eixo A": [
                _pct(pa["l1_repasse_federal"]),
                _pct(pa["l2_execucao_propria"]),
                _pct(pa["l3_contratacao_insumos"]),
            ],
        }
    )
)
for fx in conteudo.formulas_do_bloco("alocacao"):
    tema.formula(fx.titulo, fx.latex, fx.glossa)
tema.nota(
    "L1 é um <strong>proxy</strong>: o repasse fundo a fundo ao ente "
    "(<code>/transferencias</code>) responde HTTP 403 com a chave gratuita do "
    "Portal da Transparência. Usa-se, no lugar, a soma de Bolsa Família / Novo "
    "Bolsa Família + BPC por município (185/185, série completa) — dinheiro "
    "federal que chega ao território, mas não o repasse setorial de saúde.",
    tom="aviso",
    rotulo="Natureza de L1.",
)

# ── 7. Regra do cinza ────────────────────────────────────────────────
st.header("A regra do cinza")
st.markdown(
    f"""
Um eixo cuja **fração de componentes presentes** cai abaixo do limiar **não tem
IEAS calculado** — o `gap` vira NaN e o município fica cinza. Limiares:
Necessidade **{_pct(cm['necessidade'])}**, Alocação **{_pct(cm['alocacao'])}**.

O eixo Necessidade está completo (3/3) para os 185 municípios em todos os anos.
Com o L1 (Portal da Transparência) coletado para os 185, o eixo Alocação também
alcança a cobertura mínima para **921 dos 925 município-anos** — o cinza que
resta é o Distrito Estadual de Fernando de Noronha, que não tem execução própria
no SIOPS nem contratações municipais no PNCP. A coluna `l3_maturidade_pncp_uf`
do gold ainda registra, por ano, a fração de municípios presentes no PNCP: a
adesão à Lei 14.133 cresce de 2021 a 2024, e onde ela é baixa um L3 igual a zero
deve ser lido com cautela.
"""
)

# ── 8. Do eixo ao farol ──────────────────────────────────────────────
st.header("Do eixo ao farol")
for fx in conteudo.formulas_do_bloco("farol"):
    tema.formula(fx.titulo, fx.latex, fx.glossa)
st.table(
    pd.DataFrame(
        {
            "Faixa de gap": [
                f"gap ≤ {farol['vermelho_ate']}".replace(".", ","),
                f"{farol['vermelho_ate']} < gap ≤ {farol['amarelo_ate']}".replace(".", ","),
                f"|gap| ≤ {farol['verde_ate']}".replace(".", ","),
                f"gap ≥ {farol['azul_a_partir']}".replace(".", ","),
            ],
            "Farol": [tema.FAROL_ROTULO[c] for c in ("vermelho", "amarelo", "verde", "azul")],
            "Leitura": [tema.FAROL_LEITURA[c] for c in ("vermelho", "amarelo", "verde", "azul")],
        }
    )
)
st.caption(
    "A zona entre verde_ate e azul_a_partir cai no default do classificador, que "
    "também é verde — não um valor arbitrário. O cinza não é uma faixa de gap: é "
    "a ausência de gap."
)

# ── 9. Detectores ────────────────────────────────────────────────────
st.header("Os quatro detectores de anomalia")
st.markdown(
    "Varrem o cruzamento de necessidade, gasto e contratação. Cada alerta traz "
    "uma explicação em linguagem natural e é uma **suspeita para auditoria, não "
    "uma conclusão**."
)
al = dados.alertas()
por_tipo = al["tipo"].value_counts().to_dict() if not al.empty else {}
mapa_chave = {
    "d1": "desalinhamento_estrutural",
    "d2": "alocacao_abaixo_do_esperado",
    "d3": "suspeita_sobrepreco",
    "d4": "suspeita_desabastecimento",
}
for fx in conteudo.formulas_do_bloco("detectores"):
    n = por_tipo.get(mapa_chave.get(fx.chave, ""), 0)
    with st.container(border=True):
        st.markdown(f"#### {fx.titulo}")
        st.caption(f"{n} alertas no recorte")
        st.latex(fx.latex)
        st.markdown(fx.glossa)

par_alertas = conf["alertas"]
st.caption(
    f"Parâmetros: fator de IQR do sobrepreço **{par_alertas['preco_iqr_fator']}**, "
    f"limiar de resíduo robusto **{par_alertas['residuo_z_minimo']}** desvios, "
    f"percentil de incidência do desabastecimento "
    f"**{_pct(par_alertas['desabastecimento']['incidencia_percentil_minimo'])}**."
)
tema.nota(
    "O <code>seeds/agravo_insumo.yml</code> declara uma <code>janela_dias</code> "
    "entre o início do surto e a contratação esperada; o detector 4 ainda não a "
    "aplica (compara o ano inteiro). Fechar essa janela é trabalho futuro "
    "assumido.",
    rotulo="Honestidade metodológica.",
)
st.warning(conteudo.LIMITACAO_ALERTAS, icon="⚠️")

# ── 10. Decisões metodológicas ───────────────────────────────────────
st.header("Decisões que mudam o resultado")
st.markdown(
    """
- **Incidência por município de residência** (`ID_MN_RESI`), não de notificação:
  usar notificação inflaria os municípios-polo com serviço de saúde e esvaziaria
  os pequenos, invertendo o sinal que o índice existe para detectar (171/185
  municípios com dado por residência vs. 149/185 por notificação).
- **Município sem notificação = zero casos**, não dado ausente — a grade de
  185 × 5 anos é completa.
- **Rank percentil, não z-score**: robusto a *outliers* — um município pequeno
  com um hospital regional não esmaga a escala dos outros 184.
- **SIH pelo grupo RD** (AIH Reduzida): é o grupo que traz município de
  residência e diagnóstico principal — uma versão anterior concluíra, à toa, que
  nenhum grupo do SIH servia.
- **Saneamento é um retrato de 2022** aplicado a todo o recorte (Censo não é
  anual; SNIS encerrado). A coluna `saneamento_ano_referencia` deixa a
  aproximação explícita.
"""
)
st.markdown("**Correção sobre a proposta original.** " + conteudo.CORRECAO_METODOLOGICA.strip())

# ── 11. Proveniência ─────────────────────────────────────────────────
st.header("Proveniência dos dados")
f_tab = dados.fontes()
st.dataframe(
    f_tab[["nome", "camada", "licenca", "coletado", "linhas", "coletado_em", "dados_gov"]].rename(
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
st.caption("Detalhe de cada fonte — cobertura, papel e limitações — na página **Fontes**.")

tema.rodape(
    "SINAN, SIH, Censo 2022, CadÚnico, PNCP, Compras.gov.br, SIOPS, Portal da "
    "Transparência, IBGE (população, IPCA, malha)."
)

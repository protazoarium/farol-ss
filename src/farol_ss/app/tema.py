"""Identidade visual do painel — paleta, tipografia, componentes e o diagrama
de construção do índice.

Um lugar só para cor, tipografia e os elementos institucionais (cabeçalho,
rodapé, cartões, notas, molduras de fórmula, o diagrama do IEAS) que se
repetem em toda página. As páginas importam `aplicar_estilo`, `cabecalho`,
`rodape` e os helpers daqui e não repetem CSS nem HTML de layout.

A paleta do semáforo foi validada com o `validate_palette.js` da skill
dataviz (modo claro, superfície #fcfcfb, todos os pares): os quatro tons
cromáticos passam o piso de separação para daltonismo (ΔE ≥ 8 no pior par
protan/deutan) e o piso de visão normal (ΔE ≥ 15). O cinza é
deliberadamente acromático — é o estado "sem dado", não uma categoria a
mais — e por isso a cor nunca aparece sozinha: toda página que colore o
mapa também mostra o rótulo na legenda, no tooltip e na tabela.

`gap = rank(A) − rank(N)` ∈ [−1, 1]. Negativo = alocação atrás da
necessidade (subalocação); positivo = à frente (sobrealocação). O verde no
meio é o alvo, não o topo de uma escala.
"""

from __future__ import annotations

import streamlit as st

# ── Identidade ──────────────────────────────────────────────────────────
MARCA = "Farol da Saúde & Saneamento"
SIGLA = "Farol-SS"
DESCRICAO_CURTA = (
    "Índice de Efetividade da Alocação Sanitária (IEAS) para os 185 municípios de Pernambuco"
)
REPO_URL = "https://github.com/protazoarium/farol-ss"
APP_URL = "https://farol-ss.streamlit.app"

# Azul institucional (mesmo do relatório técnico em docs/relatorio-tecnico.html)
AZUL = "#1257a8"
AZUL_ESCURO = "#0d4585"
AZUL_CLARO = "#e8f0fb"
TINTA = "#191d27"
TINTA_2 = "#545c6b"
TINTA_3 = "#7f8797"
FUNDO = "#ffffff"
FUNDO_2 = "#eef1f5"
REGUA = "#dde1e8"

# ── Semáforo do farol (categórico, ordenado da pior à melhor alocação) ──
FAROL_ORDEM: list[str] = ["vermelho", "amarelo", "verde", "azul", "cinza"]

FAROL_COR: dict[str, str] = {
    "vermelho": "#c62828",  # subalocação severa: necessidade ≫ alocação
    "amarelo": "#ef6c00",  # subalocação leve
    "verde": "#00897b",  # alinhado (|gap| ≤ 0,10)
    "azul": "#1565c0",  # sobrealocação: alocação ≫ necessidade
    "cinza": "#9e9e9e",  # cobertura insuficiente — IEAS não calculado
}

FAROL_ROTULO: dict[str, str] = {
    "vermelho": "Necessidade não atendida",
    "amarelo": "Subalocação leve",
    "verde": "Alocação alinhada",
    "azul": "Alocação acima da necessidade",
    "cinza": "Sem dado suficiente",
}

FAROL_LEITURA: dict[str, str] = {
    "vermelho": "gap ≤ −0,33 — a necessidade sanitária está no topo do estado e a alocação, no fundo.",
    "amarelo": "−0,33 < gap ≤ −0,10 — a alocação fica um degrau abaixo da necessidade.",
    "verde": "|gap| ≤ 0,10 — necessidade e alocação ocupam posições próximas no ranking estadual.",
    "azul": "gap ≥ 0,33 — a alocação está bem à frente da necessidade relativa.",
    "cinza": "um dos eixos não alcançou a cobertura mínima de dados; o IEAS não é publicado.",
}

# ── Rampa sequencial azul (magnitude contínua) — steps de references/palette.md
SEQ_AZUL: list[str] = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#104281"]

CINZA_SEM_DADO = "#e6e6e3"  # município fora da camada exibida
CONTORNO = "#8a8a86"

# ── Rótulos de apoio ───────────────────────────────────────────────────
AGRAVOS: dict[str, str] = {
    "deng": "Dengue",
    "chik": "Chikungunya",
    "zika": "Zika",
    "lept": "Leptospirose",
    "hepa": "Hepatite A",
    "esqu": "Esquistossomose",
    "internacoes_drsai": "Internações (DRSAI)",
}

CAMADAS: dict[str, str] = {
    "farol": "Farol — IEAS (semáforo)",
    "necessidade_rank": "Necessidade — índice combinado (rank percentil)",
    "sub_epidemiologico": "Necessidade · carga epidemiológica (rank percentil)",
    "sub_saneamento": "Necessidade · déficit de saneamento (rank percentil)",
    "sub_vulnerabilidade": "Necessidade · vulnerabilidade social (rank percentil)",
    "alocacao_rank": "Alocação — índice combinado (rank percentil)",
    "l3_per_capita": "Alocação · contratação de insumos L3 (R$/hab)",
    "l2_per_capita": "Alocação · execução própria L2 (R$/hab)",
    "l1_per_capita": "Alocação · repasse federal L1 (R$/hab)",
}

CAMADA_UNIDADE: dict[str, str] = {
    "l1_per_capita": "reais",
    "l2_per_capita": "reais",
    "l3_per_capita": "reais",
}


def cor_sequencial(valor: float, vmin: float, vmax: float) -> str:
    """Mapeia `valor` para um dos 5 tons da rampa azul. NaN → cinza sem-dado."""
    if valor is None or vmax <= vmin or valor != valor:  # noqa: PLR0124 (NaN check)
        return CINZA_SEM_DADO
    frac = (valor - vmin) / (vmax - vmin)
    idx = min(len(SEQ_AZUL) - 1, max(0, int(frac * len(SEQ_AZUL))))
    return SEQ_AZUL[idx]


# ── Layout institucional ───────────────────────────────────────────────
_CSS = f"""
<style>
  :root {{
    --azul: {AZUL}; --azul-esc: {AZUL_ESCURO}; --azul-claro: {AZUL_CLARO};
    --regua: {REGUA}; --tinta: {TINTA}; --tinta-2: {TINTA_2}; --tinta-3: {TINTA_3};
    --fundo-2: {FUNDO_2};
  }}

  /* largura de leitura mais generosa e respiro no topo */
  .block-container {{ padding-top: 2.4rem; padding-bottom: 4.5rem; max-width: 78rem; }}
  .block-container p {{ line-height: 1.62; }}
  .block-container li {{ line-height: 1.6; }}

  h1, h2, h3, h4 {{ letter-spacing: -0.015em; }}
  h1 {{ font-weight: 700; }}
  h2 {{
    font-weight: 600; border-bottom: 1px solid var(--regua);
    padding-bottom: .35rem; margin-top: 2.6rem;
  }}
  h3 {{ font-weight: 600; color: var(--tinta); margin-top: 1.6rem; }}
  h4 {{ font-weight: 600; color: var(--tinta); }}

  a {{ color: var(--azul-esc); text-underline-offset: 2px; }}

  /* faixa institucional no topo de cada página */
  .fss-masthead {{
    border-left: 4px solid var(--azul);
    padding: .15rem 0 .15rem 1rem;
    margin-bottom: 1.5rem;
  }}
  .fss-masthead .kicker {{
    font-size: .72rem; font-weight: 700; letter-spacing: .1em;
    text-transform: uppercase; color: var(--tinta-3);
  }}
  .fss-masthead .titulo {{
    font-size: 1.8rem; font-weight: 700; line-height: 1.15; color: var(--tinta);
    margin-top: .1rem;
  }}
  .fss-masthead .sub {{
    font-size: 1rem; color: var(--tinta-2); margin-top: .35rem; max-width: 54rem;
  }}

  /* cartões de indicador */
  .fss-cards {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(148px, 1fr));
    gap: .8rem; margin: 1.1rem 0 .5rem;
  }}
  .fss-card {{
    background: var(--fundo-2); border: 1px solid var(--regua); border-radius: 10px;
    padding: .9rem 1rem;
  }}
  .fss-card .v {{
    font-size: 1.55rem; font-weight: 700; color: var(--azul-esc);
    font-variant-numeric: tabular-nums; line-height: 1.1;
  }}
  .fss-card .k {{ font-size: .78rem; color: var(--tinta-2); margin-top: .2rem; line-height: 1.35; }}

  /* selo de estado de fonte */
  .fss-pill {{
    display: inline-block; font-size: .74rem; font-weight: 600;
    padding: .12rem .55rem; border-radius: 999px;
  }}
  .fss-ok {{ background: #e0f2f1; color: #00695c; }}
  .fss-partial {{ background: #fff3e0; color: #e65100; }}
  .fss-block {{ background: #fdecea; color: #b71c1c; }}

  /* nota / callout institucional */
  .fss-note {{
    border: 1px solid var(--regua); border-left: 3px solid var(--azul);
    background: var(--azul-claro); border-radius: 8px;
    padding: .8rem 1rem; margin: 1rem 0; font-size: .92rem; color: var(--tinta);
  }}
  .fss-note.aviso {{ border-left-color: #e65100; background: #fff6ec; }}
  .fss-note.limite {{ border-left-color: #b71c1c; background: #fdeeec; }}
  .fss-note .rot {{ font-weight: 700; }}

  /* título curto acima de uma fórmula (dentro de st.container(border=True)) */
  .titf {{
    font-size: .8rem; font-weight: 700; letter-spacing: .04em;
    text-transform: uppercase; color: var(--tinta-3); margin: .1rem 0;
  }}

  /* diagrama do índice */
  .fss-diagrama {{ margin: 1.4rem 0 .6rem; }}
  .fss-diagrama img {{
    width: 100%; max-width: 720px; height: auto; display: block;
    border: 1px solid var(--regua); border-radius: 10px; background: #fff;
    padding: .6rem;
  }}
  .fss-diagrama figcaption {{
    font-size: .8rem; color: var(--tinta-3); margin-top: .5rem; max-width: 720px;
  }}

  /* tabelas mais sóbrias */
  .block-container [data-testid="stTable"] table {{ font-size: .9rem; }}
  .block-container [data-testid="stTable"] th {{ color: var(--tinta-2); }}

  .fss-rodape {{
    margin-top: 3.2rem; padding-top: 1rem; border-top: 1px solid var(--regua);
    font-size: .82rem; color: var(--tinta-3); line-height: 1.55;
  }}
  .fss-rodape a {{ color: var(--tinta-2); }}

  section[data-testid="stSidebar"] .block-container {{ padding-top: 1.6rem; }}
  section[data-testid="stSidebar"] {{ border-right: 1px solid var(--regua); }}
</style>
"""


def aplicar_estilo() -> None:
    """Injeta o CSS institucional. Chamar uma vez por página, após set_page_config."""
    st.markdown(_CSS, unsafe_allow_html=True)


def cabecalho(titulo: str, subtitulo: str, kicker: str = SIGLA) -> None:
    """Faixa institucional padronizada no topo da página."""
    st.markdown(
        f"""
        <div class="fss-masthead">
          <div class="kicker">{kicker}</div>
          <div class="titulo">{titulo}</div>
          <div class="sub">{subtitulo}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def cartoes(itens: list[tuple[str, str]]) -> None:
    """Linha de cartões de indicador — lista de (valor, rótulo)."""
    blocos = "".join(
        f'<div class="fss-card"><div class="v">{v}</div><div class="k">{k}</div></div>'
        for v, k in itens
    )
    st.markdown(f'<div class="fss-cards">{blocos}</div>', unsafe_allow_html=True)


def nota(texto: str, tom: str = "info", rotulo: str = "") -> None:
    """Callout institucional. `tom` ∈ {info, aviso, limite}."""
    classe = "" if tom == "info" else tom
    rot = f'<span class="rot">{rotulo} </span>' if rotulo else ""
    st.markdown(f'<div class="fss-note {classe}">{rot}{texto}</div>', unsafe_allow_html=True)


def formula(titulo: str, latex: str, glossa: str = "") -> None:
    """Moldura para uma fórmula: título curto, a expressão em LaTeX (KaTeX
    nativo do Streamlit) e uma glosa opcional em linguagem corrente.

    Usa `st.container(border=True)` em vez de um <div> próprio: uma `<div>`
    aberta num `st.markdown` e fechada em outro não aninha o conteúdo entre
    eles (cada markdown é um elemento isolado no Streamlit).
    """
    with st.container(border=True):
        st.markdown(
            f'<div class="titf">{titulo}</div>',
            unsafe_allow_html=True,
        )
        st.latex(latex)
        if glossa:
            st.caption(glossa)


def secao(titulo: str, texto: str) -> None:
    """Cabeçalho de seção (h3) seguido de um parágrafo introdutório."""
    st.markdown(f"### {titulo}")
    st.markdown(texto)


def rodape(fontes: str = "") -> None:
    """Rodapé institucional com licença, repositório e fontes da página."""
    linha_fontes = f"<p><strong>Fontes nesta página:</strong> {fontes}</p>" if fontes else ""
    st.markdown(
        f"""
        <div class="fss-rodape">
          {linha_fontes}
          <p>{MARCA} · {DESCRICAO_CURTA}. Dados públicos das fontes federais
          (IBGE, DATASUS, PNCP, CGU, MDS); o IEAS, o painel e a API são obra
          derivada sob domínio público.</p>
          <p>Código aberto: <a href="{REPO_URL}">{REPO_URL}</a> ·
          Concebido e implementado com Claude (Anthropic).</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Diagrama de construção do índice ──────────────────────────────────
def _svg_diagrama(pesos_n: dict[str, float], pesos_a: dict[str, float]) -> str:
    """Monta o SVG do fluxo do índice. Os pesos vêm de `conf/ieas.yml` (via
    quem chama) para o desenho nunca divergir do cálculo."""

    def p(x: float) -> str:
        return f"{x:.2f}".replace(".", ",")

    pe, ps, pv = p(pesos_n["epidemiologico"]), p(pesos_n["saneamento"]), p(pesos_n["vulnerabilidade"])
    l1 = p(pesos_a["l1_repasse_federal"])
    l2 = p(pesos_a["l2_execucao_propria"])
    l3 = p(pesos_a["l3_contratacao_insumos"])

    def chip(x, y, w, titulo, sub, cor, h=48):
        return (
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" '
            f'fill="#ffffff" stroke="{cor}" stroke-width="1.4"/>'
            f'<text x="{x + w / 2}" y="{y + 20}" text-anchor="middle" '
            f'font-size="12.5" font-weight="700" fill="{TINTA}">{titulo}</text>'
            f'<text x="{x + w / 2}" y="{y + 37}" text-anchor="middle" '
            f'font-size="10.5" fill="{TINTA_2}">{sub}</text>'
        )

    farol_seg = ""
    larg = 116
    for i, cor in enumerate(["vermelho", "amarelo", "verde", "azul", "cinza"]):
        fx = 90 + i * larg
        farol_seg += (
            f'<rect x="{fx}" y="612" width="{larg - 8}" height="34" rx="5" fill="{FAROL_COR[cor]}"/>'
            f'<text x="{fx + (larg - 8) / 2}" y="633" text-anchor="middle" '
            f'font-size="11" font-weight="700" fill="#ffffff">{cor.capitalize()}</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 690" \
font-family="-apple-system, Segoe UI, Roboto, sans-serif">
  <defs><marker id="s" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto">
    <path d="M0,0 L6,3 L0,6 Z" fill="{TINTA_3}"/></marker></defs>
  <style>
    .lig {{ stroke: {TINTA_3}; stroke-width: 1.3; marker-end: url(#s); fill: none; }}
    .rot {{ font-size: 10.5px; fill: {TINTA_3}; }}
    .eixo {{ font-size: 13px; font-weight: 700; fill: {TINTA}; }}
  </style>

  <text x="350" y="22" text-anchor="middle" class="eixo">8 fontes federais abertas · dados.gov.br</text>
  {chip(20, 34, 210, "SINAN · SIH", "notificações e internações", AZUL)}
  {chip(245, 34, 200, "Censo 2022 · CadÚnico", "saneamento e vulnerabilidade", AZUL)}
  {chip(460, 34, 220, "SIOPS · PNCP · Compras.gov", "execução própria e contratações", "#00695c")}
  {chip(120, 92, 210, "Transparência (CGU)", "repasse federal (proxy social)", "#00695c")}
  {chip(345, 92, 235, "IBGE", "população, IPCA (deflator), malha", TINTA_3)}

  <rect x="200" y="164" width="300" height="40" rx="8" fill="{FUNDO_2}" stroke="{REGUA}"/>
  <text x="350" y="189" text-anchor="middle" font-size="12.5" font-weight="700" fill="{TINTA}">
    fato município × ano — grade 185 × 5 completa</text>
  <path class="lig" d="M350,140 L350,162"/>

  <text x="185" y="246" text-anchor="middle" class="eixo">Eixo N — Necessidade</text>
  <text x="515" y="246" text-anchor="middle" class="eixo">Eixo A — Alocação</text>
  <path class="lig" d="M300,204 L210,262"/>
  <path class="lig" d="M400,204 L490,262"/>

  {chip(40, 262, 290, "Epidemiologia", f"peso {pe} · arbo + hídricas + DRSAI", FAROL_COR["vermelho"])}
  {chip(40, 320, 290, "Déficit de saneamento", f"peso {ps} · água + esgoto + lixo", FAROL_COR["amarelo"])}
  {chip(40, 378, 290, "Vulnerabilidade social", f"peso {pv} · extrema pobreza (CadÚnico)", FAROL_COR["verde"])}

  {chip(370, 262, 290, "L1 · repasse federal", f"peso {l1} · transferências sociais", "#1565c0")}
  {chip(370, 320, 290, "L2 · execução própria", f"peso {l2} · R$/hab próprios (SIOPS)", "#1565c0")}
  {chip(370, 378, 290, "L3 · contratação de insumos", f"peso {l3} · R$/hab (PNCP + Compras)", "#1565c0")}

  <text x="185" y="452" text-anchor="middle" class="rot">regra do cinza: cobertura ≥ 60%</text>
  <text x="515" y="452" text-anchor="middle" class="rot">regra do cinza: cobertura ≥ 50%</text>
  <rect x="40" y="460" width="290" height="40" rx="8" fill="#ffffff" stroke="{TINTA_3}"/>
  <text x="185" y="484" text-anchor="middle" font-size="11.5" fill="{TINTA}">
    média ponderada → rank percentil (PE)</text>
  <rect x="370" y="460" width="290" height="40" rx="8" fill="#ffffff" stroke="{TINTA_3}"/>
  <text x="515" y="484" text-anchor="middle" font-size="11.5" fill="{TINTA}">
    média ponderada → rank percentil (PE)</text>
  <path class="lig" d="M185,426 L185,458"/>
  <path class="lig" d="M515,426 L515,458"/>

  <rect x="230" y="536" width="240" height="38" rx="8" fill="{AZUL}"/>
  <text x="350" y="560" text-anchor="middle" font-size="13" font-weight="700" fill="#ffffff">
    gap = rank(A) − rank(N)</text>
  <path class="lig" d="M230,500 L320,534"/>
  <path class="lig" d="M470,500 L380,534"/>

  {farol_seg}
  <path class="lig" d="M350,574 L350,610"/>
  <text x="350" y="668" text-anchor="middle" class="rot">
    o sinal do gap escolhe a cor · |gap| só ordena (ieas = 1 − |gap|)</text>
</svg>"""


def diagrama_indice(pesos_n: dict[str, float], pesos_a: dict[str, float]) -> None:
    """Fluxo visual: fontes → dois eixos ponderados → rank percentil → gap →
    farol. Renderizado como data-URI (`<img>`) porque o Streamlit remove
    `<svg>` inline do `st.markdown`; um `<img>` com SVG embutido passa e
    escala com `max-width: 100%`.
    """
    import base64

    svg = _svg_diagrama(pesos_n, pesos_a)
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    st.markdown(
        f'<figure class="fss-diagrama">'
        f'<img src="data:image/svg+xml;base64,{b64}" alt="Como o IEAS é construído: '
        f"das oito fontes federais aos dois eixos ponderados, ao rank percentil, ao "
        f'gap e ao semáforo."/>'
        f"<figcaption>Da fonte federal ao semáforo: cada eixo é uma média ponderada "
        f"convertida em posição relativa dentro de Pernambuco. Nenhum valor absoluto "
        f"(R$, taxa) entra na cor — só o ranking.</figcaption></figure>",
        unsafe_allow_html=True,
    )

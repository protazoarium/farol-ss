"""Página Fontes — o catálogo curado das oito fontes federais.

O que cada fonte é, por que entra no IEAS, o que cobre e o que **não** cobre.
Cruza o texto institucional de `conteudo.py` com o resumo de coleta real do
`manifest.json` (via `proveniencia.tabela()`).
"""

from __future__ import annotations

import streamlit as st

from farol_ss.app import conteudo, dados, tema

st.set_page_config(page_title="Fontes · Farol-SS", page_icon="🗂️", layout="wide")
tema.aplicar_estilo()

tema.cabecalho(
    "🗂️ Fontes de dados",
    "Oito conjuntos federais abertos, todos catalogados no Portal Brasileiro de "
    "Dados Abertos. Cada ficha traz o papel no índice, a variável bruta e a "
    "transformação até o gold, a cobertura real e as limitações conhecidas.",
)

tema.nota(
    "O 2º Concurso de Reúso de Dados Abertos da CGU exige pelo menos um conjunto "
    "catalogado no dados.gov.br. O Farol-SS usa oito. A fórmula que combina tudo "
    "está na página <strong>Metodologia</strong>."
)

resumo = dados.resumo_fontes()

por_eixo: dict[str, list[conteudo.Fonte]] = {}
for f in conteudo.FONTES:
    por_eixo.setdefault(f.eixo.split(" · ")[0], []).append(f)

ordem_eixos = ["Necessidade", "Alocação", "Base"]
for eixo in ordem_eixos:
    fontes = por_eixo.get(eixo, [])
    if not fontes:
        continue
    st.header(f"Eixo {eixo}" if eixo != "Base" else "Insumos de base")
    for f in fontes:
        r = resumo.get(f.chave, {})
        linhas = r.get("linhas")
        coletado = (r.get("coletado_em") or "")[:10]

        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"#### {f.nome}")
                st.caption(f"{f.orgao} · {f.eixo}")
            with c2:
                st.markdown(
                    f'<div style="text-align:right"><span class="fss-pill '
                    f'{conteudo.PILL_CLASS[f.estado]}">{conteudo.PILL_LABEL[f.estado]}'
                    f"</span></div>",
                    unsafe_allow_html=True,
                )

            st.markdown(f"**Papel no IEAS.** {f.papel}")
            if f.variavel_bruta:
                st.markdown(f"**Variável bruta.** {f.variavel_bruta}")
            if f.transformacao:
                st.markdown(f"**Transformação até o gold.** {f.transformacao}")
            st.markdown(f"**Cobertura.** {f.cobertura}")
            if f.limitacao and f.limitacao != "—":
                st.markdown(f"**Limitação.** {f.limitacao}")

            meta = []
            if linhas:
                meta.append(f"{int(linhas):,} linhas ingeridas".replace(",", "."))
            if coletado:
                meta.append(f"última coleta {coletado}")
            meta.append(f.licenca)
            st.caption(" · ".join(meta))
            if f.dados_gov:
                st.markdown(f"[Conjunto no dados.gov.br →]({f.dados_gov})")

st.header("Proveniência técnica")
st.caption(
    "A mesma tabela que a API serve em `/fontes`: URL do conjunto, licença, "
    "contagem de linhas e data da última coleta, lida de `data/manifest.json`."
)
tab = dados.fontes()
st.dataframe(
    tab[["nome", "camada", "licenca", "coletado", "linhas", "coletado_em", "dados_gov"]].rename(
        columns={
            "nome": "Fonte",
            "camada": "Camada",
            "licenca": "Licença",
            "coletado": "Coletado",
            "linhas": "Linhas",
            "coletado_em": "Última coleta",
            "dados_gov": "dados.gov.br",
        }
    ),
    width="stretch",
    hide_index=True,
    column_config={"dados.gov.br": st.column_config.LinkColumn()},
)

st.info(
    "**Requisito do 2º Concurso de Reúso de Dados Abertos da CGU:** pelo menos "
    "um conjunto catalogado no dados.gov.br. O Farol-SS usa oito — SINAN, SIH, "
    "Censo 2022, CadÚnico, PNCP, Compras.gov.br, SIOPS e o Portal da "
    "Transparência da própria CGU.",
    icon="✅",
)

tema.rodape("todas as oito fontes federais do índice.")

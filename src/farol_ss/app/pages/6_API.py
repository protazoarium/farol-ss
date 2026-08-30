"""Página API — documenta a API aberta e oferece download direto do gold."""

from __future__ import annotations

import streamlit as st

from farol_ss.app import dados, tema

st.set_page_config(page_title="API · Farol-SS", page_icon="🔌", layout="wide")
tema.aplicar_estilo()

tema.cabecalho(
    "🔌 API aberta",
    "Todos os dados do Farol-SS são servidos sem autenticação, em JSON ou CSV, "
    "direto da camada gold. A API não recalcula nada — é a mesma tabela que o "
    "painel usa.",
)

tema.nota(
    "Sem chave, sem cadastro, sem limite de requisições. Toda rota aceita "
    "<code>?formato=json</code> (padrão) ou <code>?formato=csv</code>. Valores "
    "ausentes vêm como <code>null</code> no JSON. Documentação interativa "
    "(Swagger) em <code>/docs</code>."
)

st.markdown(
    """
```bash
# local
uv run uvicorn farol_ss.api.main:api --port 8000     # ou: make api
```
"""
)

st.header("Rotas")
st.table(
    {
        "método": ["GET"] * 5,
        "rota": [
            "/municipios",
            "/municipios/{cod_ibge}",
            "/ieas?ano=2024&farol=vermelho",
            "/alertas?tipo=suspeita_desabastecimento&ano=2024",
            "/fontes",
        ],
        "descrição": [
            "os 185 municípios de PE, com meso/microrregião e região intermediária",
            (
                "série completa de um município — todas as colunas do IEAS por ano "
                "(população, casos, taxas, L1/L2/L3, subíndices, cobertura, gap, "
                "farol); 404 se o código não for de PE"
            ),
            (
                "IEAS por município-ano, projetado nas colunas de leitura (ranks, "
                "coberturas, gap, ieas, farol, l3_maturidade_pncp_uf, "
                "saneamento_ano_referencia); filtros ano (2020–2024) e farol"
            ),
            "alertas explicáveis dos quatro detectores; filtros tipo e ano",
            (
                "catálogo + proveniência (conjunto no dados.gov.br, licença, "
                "linhas, última coleta)"
            ),
        ],
    }
)

st.header("Exemplos")
st.code(
    "curl 'http://localhost:8000/ieas?ano=2024&formato=csv' -o ieas_2024.csv\n"
    "curl 'http://localhost:8000/municipios/2611606'            # Recife\n"
    "curl 'http://localhost:8000/alertas?ano=2024' | jq '.[0]'\n"
    "curl 'http://localhost:8000/fontes'                        # proveniência",
    language="bash",
)

st.header("Download direto (camada gold)")
c1, c2, c3 = st.columns(3)
c1.download_button(
    "IEAS — CSV",
    dados.ieas().to_csv(index=False).encode("utf-8"),
    file_name="ieas.csv",
    mime="text/csv",
)
c2.download_button(
    "Fato município × ano — CSV",
    dados.fato().to_csv(index=False).encode("utf-8"),
    file_name="fato_municipio_ano.csv",
    mime="text/csv",
)
al = dados.alertas()
c3.download_button(
    "Alertas — CSV",
    al.to_csv(index=False).encode("utf-8"),
    file_name="alertas.csv",
    mime="text/csv",
    disabled=al.empty,
)

st.caption(
    "O Streamlit Community Cloud roda apenas Streamlit; para publicar a API use "
    "um serviço ASGI (Render, Railway, Fly.io, Cloud Run) — ver `docs/deploy.md`."
)

tema.rodape()

"""Página API — documenta a API aberta e oferece download direto do gold."""

from __future__ import annotations

import streamlit as st

from farol_ss.app import dados

st.set_page_config(page_title="API · Farol-SS", page_icon="🔌", layout="wide")

st.title("🔌 API aberta")
st.markdown(
    """
Todos os dados do Farol-SS são servidos sem autenticação, em JSON ou CSV,
direto da camada gold. A API não recalcula nada — é a mesma tabela que o
painel usa.

```bash
uv run uvicorn farol_ss.api.main:api --port 8000   # ou: make api
```

Swagger interativo em **`http://localhost:8000/docs`**.
"""
)

st.header("Rotas")
st.markdown(
    """
| Método | Rota | Descrição |
|---|---|---|
| GET | `/municipios` | os 185 municípios de PE (dimensão) |
| GET | `/municipios/{cod_ibge}` | série completa de um município |
| GET | `/ieas?ano=2024&farol=vermelho` | IEAS por município-ano, filtrável |
| GET | `/alertas?tipo=suspeita_desabastecimento&ano=2024` | alertas explicáveis |
| GET | `/fontes` | catálogo + proveniência (dados.gov.br, licença, última coleta) |

Qualquer rota aceita **`?formato=csv`**.
"""
)

st.header("Exemplos")
st.code(
    "curl 'http://localhost:8000/ieas?ano=2024&formato=csv' -o ieas_2024.csv\n"
    "curl 'http://localhost:8000/municipios/2611606'            # Recife\n"
    "curl 'http://localhost:8000/alertas?ano=2024' | jq '.[0]'",
    language="bash",
)

st.header("Download direto (camada gold)")
c1, c2, c3 = st.columns(3)
c1.download_button(
    "IEAS (todos os anos) — CSV",
    dados.ieas().to_csv(index=False).encode("utf-8"),
    file_name="ieas.csv",
    mime="text/csv",
)
c2.download_button(
    "Fato município × ano — CSV",
    dados.ieas().to_csv(index=False).encode("utf-8"),
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
    "Licença: dados públicos das fontes federais. IEAS e painel são obra derivada sob domínio público."
)

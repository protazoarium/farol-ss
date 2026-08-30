# Deploy do painel no Streamlit Community Cloud

O painel é estático em relação a dados: lê só os Parquet de `data/gold/` e
`data/silver/` versionados no repositório. Não roda o pipeline nem chama API
externa em runtime. Isso torna o deploy trivial — mas exige que os arquivos
derivados estejam commitados.

## O que já está preparado no repositório

| Arquivo | Papel |
|---|---|
| `requirements.txt` | dependências de runtime do painel — só a base leve (`-e .`), sem `geopandas`, `pysus`, `fastapi`, `typer` |
| `.streamlit/config.toml` | tema claro, `gatherUsageStats = false` |
| `.gitignore` | versiona só os ~1,7 MB de Parquet que o painel lê (o resto de `data/` continua ignorado) |
| `pyproject.toml` | dependências divididas em base + extras `pipeline` / `api` / `sus` / `dev` |

Os dados versionados para o deploy:

```
data/manifest.json
data/bronze/ibge_malhas.parquet
data/silver/epidemiologia.parquet
data/silver/pncp.parquet
data/gold/fato_municipio_ano.parquet
data/gold/ieas.parquet
data/gold/alertas.parquet
```

Regenerar a qualquer momento com `make silver gold ieas` e commitar de novo.

## Passos (você — precisa das suas contas)

1. **Push do repositório para o GitHub** (público ou privado; o Streamlit
   Cloud acessa os dois com o app OAuth).
   ```bash
   git remote add origin git@github.com:<voce>/farol-ss.git
   git push -u origin main
   ```
2. Entrar em **<https://share.streamlit.io>** com a conta GitHub.
3. **New app → From existing repo**:
   - Repository: `<voce>/farol-ss`
   - Branch: `main`
   - **Main file path**: `src/farol_ss/app/Home.py`
   - Advanced settings → **Python version: 3.12**
4. **Deploy**. O primeiro build leva ~3–5 min (instala o `requirements.txt`).

Não há `secrets` a configurar — o painel não usa chave de API.

## Verificação pós-deploy

- A página **Farol** deve abrir na camada "Necessidade" com o mapa colorido.
- A página **Metodologia** deve listar a tabela de proveniência com os links
  para o `dados.gov.br`.
- Se o mapa não renderizar: confirme que `data/bronze/ibge_malhas.parquet` foi
  para o repositório (`git ls-files data/`).

## Atualizar os dados no ar

```bash
make ingest            # se quiser dados novos das fontes
make silver gold ieas  # regenera os derivados
git add data/ && git commit -m "atualiza recorte de dados" && git push
```

O Streamlit Cloud redeploya sozinho a cada push na branch.

## A API FastAPI

O Streamlit Community Cloud roda **apenas Streamlit** — a API (`make api`) não
sobe lá. Para publicá-la, use um serviço que rode um processo ASGI
(Render, Railway, Fly.io, Cloud Run) com:

```bash
pip install -e ".[api]"
uvicorn farol_ss.api.main:api --host 0.0.0.0 --port $PORT
```

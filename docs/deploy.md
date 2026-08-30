# Deploy do painel no Streamlit Community Cloud

O painel é estático em relação a dados: lê só os Parquet de `data/gold/` e
`data/silver/` versionados no repositório. Não roda o pipeline nem chama API
externa em runtime. Isso torna o deploy trivial — mas exige que os arquivos
derivados estejam commitados (já estão, no `main`).

## O que já está preparado no repositório

| Arquivo | Papel |
|---|---|
| `requirements.txt` | dependências de runtime do painel — só a base leve (`-e .`), sem `geopandas`, `pysus`, `fastapi`, `typer` |
| `.streamlit/config.toml` | tema claro institucional (`base = "light"`, azul `#1257a8`), `gatherUsageStats = false` |
| `.gitignore` | versiona só os ~1,7 MB de Parquet que o painel lê (o resto de `data/` continua ignorado) |
| `pyproject.toml` | dependências divididas em base + extras `pipeline` / `api` / `sus` / `dev` |

Os dados versionados para o deploy (o `.gitignore` versiona só estes ~1,7 MB):

```
data/manifest.json
data/bronze/ibge_malhas.parquet
data/silver/{epidemiologia, sih, pncp, pncp_itens, compras_gov,
             siops, cadunico, transparencia, ibge_saneamento}.parquet
data/gold/{fato_municipio_ano, ieas, alertas}.parquet
```

Estado atual (v1.4): as oito fontes ingeridas, **L1 completo** (185/185 × 5
anos), IEAS calculado para 921 dos 925 município-anos, 777 alertas. Regenerar a
qualquer momento com `make silver gold ieas` e commitar de novo.

---

## Passo 1 — o repositório já está no GitHub

`https://github.com/protazoarium/farol-ss`, branch `main`, público. O último
commit já traz o painel redesenhado e os dados de v1.4. Se fizer mudanças
locais, `git push origin main` — o Streamlit Cloud redeploya sozinho a cada
push.

## Passo 2 — entrar no Streamlit Community Cloud

Acesse **<https://share.streamlit.io>**. A tela de login oferece três botões:
**Continue with Google**, **Continue with GitHub**, **Continue with email**.

**Caminho recomendado (contorna o erro de login por GitHub):**

1. Clique em **Continue with Google** e entre com `protazoario@gmail.com`.
2. Já dentro, clique no seu nome (canto da tela) → **Workspace settings** →
   aba **Linked accounts**.
3. Em **Source control**, clique **Connect GitHub account**.
4. O GitHub abre a autorização do app OAuth **"Streamlit"** — clique
   **Authorize streamlit**. Como o repositório `protazoarium/farol-ss` está na
   sua conta pessoal (não numa organização), não há aprovação de terceiros a
   esperar.

### Se a tela travar ou entrar em loop de redirecionamento

Quase sempre é cookie de terceiros ou extensão de navegador:

- Abra uma **janela anônima do Chrome** (sem extensões) e tente de novo.
- Permita cookies de terceiros para `streamlit.io` e `github.com`.
- Desligue VPN/proxy durante o login.
- Se "Continue with GitHub" falhar, faça o contrário: entre com Google/e-mail
  primeiro e conecte o GitHub depois (passos acima).

## Passo 3 — criar o app

1. **Create app** → **Deploy a public app from GitHub**.
2. Preencha:
   - **Repository**: `protazoarium/farol-ss`
   - **Branch**: `main`
   - **Main file path**: `src/farol_ss/app/Home.py`
   - **App URL**: `farol-ss` → gera `https://farol-ss.streamlit.app` (é essa a
     URL registrada nos formulários do concurso; ver `docs/publicacao-reuso.md`)
   - **Advanced settings → Python version: 3.12**
3. **Deploy**. O primeiro build leva ~3–5 min (instala o `requirements.txt`).

Não há `secrets` a configurar — o painel não usa chave de API.

## Passo 4 — deixar o app público

O `farol-ss.streamlit.app` precisa abrir **sem login** para servir como URL do
reúso. Depois do deploy: **Manage app** (canto inferior direito) → **Settings**
→ **Sharing** → garanta **"This app is public and searchable"** (ou equivalente:
qualquer pessoa pode ver). Teste numa janela anônima: deve carregar a Home sem
pedir conta.

---

## Verificação pós-deploy

- A **Home** mostra os cinco cartões do recorte, o **diagrama de construção do
  índice** (SVG), o semáforo e a lista das oito fontes com o selo de estado.
- A página **Farol** abre com o mapa colorido (921/925 município-anos têm cor;
  o seletor de camada troca entre o Farol e cada subíndice/camada de gasto).
- A página **Metodologia** renderiza as fórmulas em notação matemática
  (`st.latex` / KaTeX): rank percentil, deflator, os subíndices, `gap`/`ieas`,
  os quatro detectores. Se aparecerem como texto cru `\frac{...}`, o KaTeX não
  carregou — recarregue a página.
- A página **Fontes** lista as oito fichas (variável bruta → transformação) e a
  tabela de proveniência com os links para o `dados.gov.br`.
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

A URL do reúso no concurso é a do painel; a API é um complemento opcional.

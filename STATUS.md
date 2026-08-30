# Farol-SS — estado do projeto

**Atualizado**: 2026-08-30 | Pipeline completo end-to-end; painel e API prontos.

Relatório técnico detalhado (pipeline, decisões metodológicas, resultados,
limitações): **`docs/relatorio-tecnico.md`**.

## Pronto ✅

| Bloco | Nota |
|---|---|
| Scaffold, config, seeds | 185 municípios, pesos/limiares em `conf/ieas.yml` |
| Spike de 12 fontes | 3 endpoints do plano original corrigidos |
| Ingestão IBGE | população, IPCA (deflator), malha municipal |
| Ingestão SINAN | 6 agravos × 5 anos, 271.505 notificações, 185/185 municípios |
| Ingestão PNCP | 6.150 contratos + 4.691 itens com preço unitário; 172/185 municípios |
| Ingestão SIOPS (L2) | execução própria em saúde R$/hab via TabNet legado; 184/185 × 5 anos |
| Ingestão CadÚnico (vulnerabilidade) | taxa de extrema pobreza via SAGI/MDS (Solr); 185/185 × 5 anos |
| Silver | `epidemiologia.parquet` (3.111) + `pncp.parquet` (6.150) |
| Gold | `fato_municipio_ano.parquet` — 925 linhas, grão único, L3 deflacionado p/ 2024 |
| IEAS | **calculado para 335/925 município-anos** (era 0); 2024: 156/185 com cor |
| Detectores | 1, 3 e 4 ativos — 677 alertas (581 desabastecimento, 92 desalinhamento, 4 sobrepreço) |
| Painel Streamlit | 6 páginas: Home, Farol, Município, Alertas, Metodologia, API |
| API FastAPI | `/municipios`, `/ieas`, `/alertas`, `/fontes` — JSON/CSV, sem auth |
| Testes | 59 passando (`uv run pytest -q`) |
| Paleta do mapa | validada p/ daltonismo (`dataviz/scripts/validate_palette.js`, modo claro) |
| Deploy do painel | arquivos prontos: `requirements.txt` (base leve), `.gitignore` versiona ~1,7 MB de Parquet, `docs/deploy.md`. Falta o push + "New app" no Streamlit Cloud (contas do autor). |
| Dependências | pyproject dividido: base (painel/API) + extras `pipeline` / `api` / `sus` / `dev` |

## Bloqueado / pendente

| Fonte | Eixo | Situação | Efeito |
|---|---|---|---|
| Portal da Transparência | A · L1 | `/transferencias` dá 403 (exige nível gov.br); mas `bolsa-familia-por-municipio`, `auxilio-emergencial-por-municipio` e `convenios` respondem 200 | Alocação fica em 2 de 3 camadas; L1 parcial viável |
| SNIS | N · saneamento | sistema encerrado em 2023 (→ SINISA, sem série municipal); domínio da série histórica não resolve | Necessidade fica em 2 de 3 subíndices; substituir por Censo 2022 IBGE |

**Consequência**: os dois eixos passam o limiar de cobertura para **335 dos 925
município-anos** (156 dos 185 municípios em 2024) — o farol tem cor. Os cinza
restantes são, sobretudo, município-anos sem contratação no PNCP (a camada L3
sobe de 6 municípios em 2021 para 157 em 2024).

## Comandos

```bash
make install            # uv sync --all-extras
make spike | ingest | silver | gold | ieas | all
farol ingest-itens      # itens do PNCP (preço unitário; retomável)
make app                # painel Streamlit
make api                # API aberta
make test | lint
```

## Próximos passos

1. **L1** (Portal da Transparência): montar um L1 parcial com Bolsa Família +
   Auxílio Emergencial + convênios (endpoints que respondem 200) para fechar a
   Alocação em 3 de 3.
2. **Saneamento**: subíndice via abastecimento de água / esgoto / lixo do
   Censo 2022 do IBGE (substituto do SNIS), fechando a Necessidade em 3 de 3.
3. **Deploy**: repo em `github.com/protazoarium/farol-ss`; falta o "New app" no
   Streamlit Community Cloud (`docs/deploy.md`).
4. Detector 3: normalizar preço por unidade de medida; rodar `farol
   ingest-itens` completo.

# Farol-SS — estado do projeto

**Atualizado**: 2026-08-30 (v1.4) | Pipeline completo; 8 fontes; L1 completo; os 4 detectores ativos.

Relatório técnico detalhado (pipeline, decisões metodológicas, resultados,
limitações): **`docs/relatorio-tecnico.md`**.

## Pronto ✅

| Bloco | Nota |
|---|---|
| Scaffold, config, seeds | 185 municípios, pesos/limiares em `conf/ieas.yml` |
| Ingestão IBGE | população, IPCA (deflator), malha municipal |
| Ingestão SINAN | 6 agravos × 5 anos, 271.505 notificações, 185/185 municípios |
| Ingestão SIH-SUS | grupo RD (AIH Reduzida) — internações DRSAI, 22.597 no recorte, 185/185 × 5 anos |
| Ingestão PNCP | 6.150 contratos + 4.691 itens com preço unitário; 172/185 municípios |
| Ingestão Compras.gov.br (L3 federal) | 858 contratações federais de saúde em PE (esfera F), 10 municípios, 2021–2024 |
| Ingestão SIOPS (L2) | execução própria em saúde R$/hab via TabNet legado; 184/185 × 5 anos |
| Ingestão CadÚnico (vulnerabilidade) | taxa de extrema pobreza via SAGI/MDS (Solr); 185/185 × 5 anos |
| Ingestão saneamento (N) | déficit água/esgoto/lixo do Censo 2022; 185/185 (`saneamento_ano_referencia = 2022`) |
| Ingestão L1 (Transparência) | transf. sociais federais por município (proxy — Bolsa Família/Novo BF + BPC); **185/185 × 5 anos, coleta completa** |
| Silver | um Parquet por domínio, grão `(cod_ibge, ano)` |
| Gold | `fato_municipio_ano.parquet` — 925 linhas, grão único, L1/L2/L3 deflacionados p/ 2024; colunas de confiança `l3_maturidade_pncp_uf` e `saneamento_ano_referencia` |
| IEAS | Necessidade completa (3/3) para os 185; **921/925 município-anos com cor** (2024: 185/185; os 4 cinza são Fernando de Noronha, sem SIOPS/PNCP municipais) |
| Detectores | **os 4 ativos** — 777 alertas (570 desabast., 202 desalinh., 4 resíduo-regressão, 1 sobrepreço) |
| Detector 3 | agora separa preços por (categoria, unidade, **dose/concentração**) — `_dose_norm` |
| Detector 4 | agora cruza incidência com **objeto E itens** das contratações, não só o objeto |
| Painel Streamlit | sistema de design institucional (`app/tema.py` + `app/conteudo.py`): cabeçalho, cartões, notas, molduras de fórmula, diagrama SVG do índice e CSS compartilhados. Home + 6 páginas. A **Metodologia** apresenta todas as fontes (variável bruta → transformação) e todas as fórmulas em `st.latex` (KaTeX), com os parâmetros lidos de `conf/ieas.yml`. URL de publicação: `https://farol-ss.streamlit.app` |
| API FastAPI | `/municipios`, `/ieas`, `/alertas`, `/fontes` — JSON/CSV, sem auth; `/ieas` expõe as colunas de confiança |
| Testes | **75 passando** (`uv run pytest -q`) |
| Paleta do mapa | validada p/ daltonismo (modo claro) |
| Deploy do painel | arquivos prontos; falta o push + "New app" no Streamlit Cloud (conta do autor) |

## Limitações que permanecem (documentadas)

| Item | Situação |
|---|---|
| L1 fundo a fundo | `/transferencias` (repasse setorial ao ente) dá HTTP 403 permanente com a chave gratuita — testadas as duas variantes. Usa-se transferências sociais (Bolsa Família/Novo BF + BPC) como proxy; a **cobertura é completa** (185/185 × 5 anos), a limitação é de natureza, não de coleta. |
| Saneamento | Censo 2022 é retrato único (SNIS encerrado, sem série municipal). Marcado em `saneamento_ano_referencia`. |
| Cobertura do PNCP no tempo | adesão à Lei 14.133 cresce ano a ano; o snapshot tem modalidade-anos coletados parcialmente (PNCP instável). `l3_maturidade_pncp_uf` é o indicador de confiança. Re-ingestão resiliente = trabalho futuro. |
| Casamento compra × insumo | palavra-chave curada (`seeds/catmat_saude.csv`), não CATMAT estruturada — o PNCP não expõe a categoria do item (`itemCategoriaNome` = "Não se aplica" em 100%). Alertas são suspeitas para auditoria. |

## Comandos

```bash
make install            # uv sync --all-extras
make spike | ingest | silver | gold | ieas | all
farol ingest-sih        # SIH-SUS (grupo RD)
farol ingest-l3-federal  # Compras.gov.br (L3 federal)
farol ingest-itens       # itens do PNCP (preço unitário; retomável)
farol ingest-l1          # L1 (Transparência) — retomável
make app | api | test | lint
```

## Próximos passos

1. **Deploy** no Streamlit Community Cloud (`docs/deploy.md`) — repo em
   `github.com/protazoarium/farol-ss`.
2. **Inscrição no concurso da CGU** até 11/09/2026 — checklist em
   `docs/concurso-cgu.md` e valores dos formulários em `docs/publicacao-reuso.md`.
3. Re-ingestão resiliente do PNCP (paginação por modalidade-ano tolerante a
   páginas instáveis) e equivalência farmacêutica no detector 3.
4. Fechar a `janela_dias` do detector 4 (hoje compara o ano inteiro; o
   `seeds/agravo_insumo.yml` já declara a janela esperada por agravo).

# Farol-SS — estado do projeto

**Atualizado**: 2026-08-29 | Pipeline completo end-to-end; painel e API prontos.

Relatório técnico detalhado (pipeline, decisões metodológicas, resultados,
limitações): **`docs/relatorio-tecnico.md`**.

## Pronto ✅

| Bloco | Nota |
|---|---|
| Scaffold, config, seeds | 185 municípios, pesos/limiares em `conf/ieas.yml` |
| Spike de 12 fontes | 3 endpoints do plano original corrigidos |
| Ingestão IBGE | população, IPCA (deflator), malha municipal |
| Ingestão SINAN | 6 agravos × 5 anos, 271.505 notificações, 185/185 municípios |
| Ingestão PNCP | 6.150 contratos, 172/185 municípios, 2021–2024, R$ 3,28 bi homologados |
| Silver | `epidemiologia.parquet` (3.111) + `pncp.parquet` (6.150) |
| Gold | `fato_municipio_ano.parquet` — 925 linhas, grão único, L3 deflacionado p/ 2024 |
| IEAS | 2 eixos, rank percentil, gap, semáforo, regra do cinza |
| Detectores | 1 (desalinhamento estrutural) + 4 (suspeita de desabastecimento, 548 alertas) |
| Painel Streamlit | 6 páginas: Home, Farol, Município, Alertas, Metodologia, API |
| API FastAPI | `/municipios`, `/ieas`, `/alertas`, `/fontes` — JSON/CSV, sem auth |
| Testes | 51 passando (`uv run pytest -q`) |
| Paleta do mapa | validada p/ daltonismo (`dataviz/scripts/validate_palette.js`, modo claro) |
| Deploy do painel | arquivos prontos: `requirements.txt` (base leve), `.gitignore` versiona ~1,7 MB de Parquet, `docs/deploy.md`. Falta o push + "New app" no Streamlit Cloud (contas do autor). |
| Dependências | pyproject dividido: base (painel/API) + extras `pipeline` / `api` / `sus` / `dev` |

## Bloqueado / pendente

| Fonte | Eixo | Situação (recon 29/08) | Efeito |
|---|---|---|---|
| Portal da Transparência | A · L1 | chave **funciona** p/ `bolsa-familia-por-municipio`, `auxilio-emergencial-por-municipio`, `convenios`; só `/transferencias` dá 403 (nível gov.br) | L1 parcial é viável |
| SIOPS | A · L2 | site responde; série histórica por TabNet/CSV, link de extração a garimpar | eixo A em 33% |
| SNIS | N · saneamento | sistema encerrado em 2023 (→ SINISA); sem mirror funcional. Rotas: Base dos Dados ou Censo 2022 IBGE | eixo N em 33% |
| CadÚnico | N · vulnerabilidade | SAGI migrou (endpoints antigos 404); URL atual a localizar | idem |

**Consequência**: os dois eixos ficam abaixo da cobertura mínima
(`conf/ieas.yml`: N 60%, A 50%), então **o IEAS não é calculado e o farol é
100% cinza** — a regra do cinza funcionando como projetada. O pipeline
inteiro roda e passa a colorir sozinho quando L1/L2/saneamento entrarem.

## Comandos

```bash
make spike | ingest | silver | gold | ieas | all
make app                # painel Streamlit
make api                # API aberta
make test | lint
```

## Próximos passos (fora do escopo desta entrega)

1. Destravar SIOPS (download da série histórica de indicadores municipais) —
   é a fonte de Alocação mais viável e destrava as cores do farol.
2. Reabrir o Portal da Transparência (investigar o 403 além do delay de
   propagação da chave).
3. Coletar SNIS por mirror alternativo (`dadosabertos.cidades.gov.br`).
4. Deploy do painel (Streamlit Community Cloud) para a submissão do concurso.

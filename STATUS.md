# Farol-SS Implementation Status

**Date**: 2026-08-25 | **Phase**: MVP pipeline complete, awaiting financial data

## Completed ✅

- [x] Etapa 1: Scaffold + Config (pyproject.toml, Makefile, CLI)
- [x] Etapa 2: Spike validation (11/12 sources; 3 endpoints corrected)
- [x] Etapa 3: Data ingest (IBGE, SINAN, PNCP partial)
- [x] Etapa 4: Silver layer (epidemiologia consolidated)
- [x] Etapa 5: Seeds curated (agravo→insumo, CID, CATMAT)
- [x] Etapa 6: Gold layer (925 rows, 185×5, no orphans)
- [x] Etapa 7: IEAS calculation (2 eixos, rank percentil, semáforo)
- [x] Etapa 8: Anomaly detection (4 detectors, 2 implemented)
- [x] Tests (43 passing, regressão + fixtures)
- [x] Bootstrap script (consolidate_e_recalcula.sh)

## Blocked 🔴

| Source | Issue | Workaround |
|---|---|---|
| Transparência (L1) | HTTP 403 | Manual coleta ou propagação delay |
| SIOPS (L2) | No real API | TabNet legado, scraping needed |
| SNIS | DNS failure | `app4.mdr.gov.br` offline |
| CadÚnico (vulnerability) | Not started | Next priority if funds available |

## Current Data State

```
data/
├── silver/
│   ├── ibge_*.parquet (population, IPCA, malhas) ✓
│   ├── sinan_*.parquet (30 files, 6 agravos, 5 anos) ✓
│   ├── epidemiologia.parquet (consolidated, 3,111 rows) ✓
│   ├── pncp_*.parquet (7 files, still ingesting) 🔄
│   └── pncp.parquet (consolidated partial, 4,549 rows) ✓
├── gold/
│   ├── fato_municipio_ano.parquet (925 rows) ✓
│   └── ieas.parquet (all cinza, pending L1+L2+SNIS) ✓
└── manifest.json (proveniência) ✓
```

## To Finish MVP

1. **Immediate** (when PNCP ingest completes):
   ```bash
   scripts/consolidate_e_recalcula.sh  # Rebuilds gold+IEAS with complete L3
   ```

2. **Next session** (Etapas 9-10):
   - Streamlit painel (5 pages: farol, drill-down, alertas, metodologia, API docs)
   - FastAPI service (JSON/CSV endpoints)
   - Paleta de cores segura para daltonismo (via dataviz skill)

3. **Optional enhancements**:
   - SIOPS scraping (if time allows)
   - Detectores 2-3 (quando L1+L2 chegarem)
   - CadÚnico integração

## Key Lessons Embedded

**See `memory/data-pipeline-silent-bugs.md` for three critical corrections:**
- `.lstrip("260")` corromped 22/185 codes
- `pysus.sinan(as_dataframe=True)` OOM-killed at 6.4GB
- `.drop_duplicates()` lost 66% of case data

All caught by real-data testing, fixed with regression tests.

## Commands

```bash
make spike              # Validate source accessibility
make ingest             # Fetch IBGE, SINAN, PNCP
make silver             # Consolidate epidemiologia
make gold               # Join into grão único
make ieas               # Calculate IEAS + alertas
make all                # Complete pipeline

make test               # 43 tests
make lint               # ruff check + format

scripts/consolidate_e_recalcula.sh  # Final step when PNCP done
```

## Commits

- **07e5f6e**: MVP pipeline end-to-end (41 files, 6023 insertions)
- **437e84b**: PNCP silver consolidation module
- **8fc17a3**: Bootstrap script for PNCP completion

## Next Session Checklist

- [ ] Check if PNCP ingest finished (`ps aux | grep farol ingest`)
- [ ] If yes, run `scripts/consolidate_e_recalcula.sh`
- [ ] Verify IEAS shows real colors (not all cinza)
- [ ] Build Streamlit pages (start with Farol map)
- [ ] Use dataviz skill for color palette

---

**Repository**: `/home/pedro/reuso_projeto/` | **Submissions ready at**: Etapas 1–8

#!/usr/bin/env bash
# Gera docs/relatorio-tecnico.docx a partir de docs/relatorio-tecnico.md,
# em formato acadêmico (página de rosto, sumário, seções numeradas).
# Requer: pandoc.
set -euo pipefail
cd "$(dirname "$0")/.."

SRC="docs/relatorio-tecnico.md"
OUT="docs/relatorio-tecnico.docx"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# 1. Página de rosto + metadados pandoc.
cat > "$TMP/meta.md" <<'EOF'
---
title: "Farol da Saúde & Saneamento"
subtitle: "Relatório Técnico — Índice de Efetividade da Alocação Sanitária (IEAS) para os 185 municípios de Pernambuco"
author: "Concebido e implementado com Claude (Anthropic)"
date: "Versão 1.1 · 30 de agosto de 2026"
lang: pt-BR
abstract: |
  O Farol-SS é um monitor territorial que cruza execução financeira em saúde
  com carga epidemiológica e vulnerabilidade social para os 185 municípios de
  Pernambuco (2020–2024), produzindo o IEAS — Índice de Efetividade da Alocação
  Sanitária, um índice de alinhamento territorial entre o quanto um município
  precisa e o quanto recebe/gasta. Este relatório detalha o pipeline de dados
  (ingestão → silver → gold → índice → alertas), a metodologia do índice, os
  detectores de anomalia, a camada de apresentação (painel web e API aberta) e
  os resultados: cinco fontes federais abertas alimentam o índice, que é
  calculado para 335 dos 925 município-anos. Documenta também os bloqueios de
  fonte encontrados e as soluções adotadas (raspagem do TabNet legado do SIOPS,
  índice Solr do SAGI para o CadÚnico, recurso de item do PNCP para preço
  unitário) e três classes de bug de corrupção silenciosa detectadas apenas
  contra dado real.
keywords: "dados abertos; saúde pública; contratações públicas; PNCP; SINAN; SIOPS; CadÚnico; índice territorial; arquitetura lakehouse; DuckDB"
---
EOF

# 2. Corpo: descarta o título H1, o subtítulo e a seção "## Resumo"
#    (viraram metadados/abstract); começa em "## 1. Motivação e objetivo".
sed -n '/^## 1\. Motiva/,$p' "$SRC" > "$TMP/body.md"

cat "$TMP/meta.md" "$TMP/body.md" > "$TMP/full.md"

# 3. Conversão. As seções do .md já são numeradas manualmente (1, 2, 2.1…),
#    então não usamos --number-sections; só promovemos ## → # para virarem
#    Título 1 no Word.
pandoc "$TMP/full.md" \
  --from=gfm+yaml_metadata_block \
  --to=docx \
  --output="$OUT" \
  --toc --toc-depth=3 \
  --shift-heading-level-by=-1 \
  --metadata=toc-title:"Sumário"

echo "✓ $OUT ($(du -h "$OUT" | cut -f1))"

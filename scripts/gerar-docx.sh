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
author: ""
date: "Versão 1.4 · 30 de agosto de 2026"
lang: pt-BR
abstract: |
  O Farol-SS é um monitor territorial que cruza execução financeira em saúde
  com carga epidemiológica, déficit sanitário e vulnerabilidade social para os
  185 municípios de Pernambuco (2020–2024), produzindo o IEAS — Índice de
  Efetividade da Alocação Sanitária, um índice de alinhamento territorial entre
  o quanto um município precisa e o quanto recebe/gasta. Este relatório detalha
  o pipeline de dados (ingestão → silver → gold → índice → alertas), a
  metodologia do índice, os quatro detectores de anomalia, a camada de
  apresentação (painel web e API aberta) e os resultados. Oito fontes federais
  abertas alimentam o índice: SINAN e SIH (epidemiologia), Censo 2022 do IBGE
  (saneamento), CadÚnico/SAGI (vulnerabilidade), PNCP e Compras.gov.br (L3),
  SIOPS (L2), Portal da Transparência (L1, proxy — 185/185) e IBGE (população,
  IPCA, malha). Documenta também os bloqueios de fonte encontrados e as
  soluções adotadas — incluindo a correção da conclusão errada do spike sobre
  o SIH — e três classes de bug de corrupção silenciosa detectadas apenas
  contra dado real.
keywords: "dados abertos; saúde pública; contratações públicas; PNCP; SINAN; SIH; SIOPS; CadÚnico; índice territorial; arquitetura lakehouse; DuckDB"
---
EOF

# 2. Corpo: descarta o título H1, o subtítulo e a seção "## Resumo"
#    (viraram metadados/abstract); começa em "## 1. Motivação e objetivo".
sed -n '/^## 1\. Motiva/,$p' "$SRC" > "$TMP/body.md"

# 3. Sumário estático (as seções já são numeradas à mão no .md). Linhas com
#    quebra forte (\) e ponto escapado, para o Word não renumerar sozinho e
#    não depender de "atualizar campos".
{
  echo "## Sumário"
  echo
  grep -E '^#{2,3} ' "$TMP/body.md" | sed -E \
    -e 's/^### ([0-9]+)\.([0-9]+) /\&nbsp;\&nbsp;\&nbsp;\&nbsp;\1.\2 /' \
    -e 's/^## ([0-9]+)\. /\1\\. /' \
    -e 's/^## //' \
    -e 's/$/\\/'
  echo
  # quebra de página antes do corpo (OpenXML bruto, entendido pelo Word)
  printf '```{=openxml}\n<w:p><w:r><w:br w:type="page"/></w:r></w:p>\n```\n'
  echo
} > "$TMP/toc.md"

cat "$TMP/meta.md" "$TMP/toc.md" "$TMP/body.md" > "$TMP/full.md"

# 4. Conversão. Promove ## → # para virarem Título 1 no Word; sem
#    --number-sections (a numeração 1, 2, 2.1… já está no texto).
pandoc "$TMP/full.md" \
  --from=markdown+pipe_tables+yaml_metadata_block+raw_attribute \
  --to=docx \
  --output="$OUT" \
  --shift-heading-level-by=-1

echo "✓ $OUT ($(du -h "$OUT" | cut -f1))"

#!/usr/bin/env python3
"""04 — gera o esqueleto do fichamento em RIS (fichamento.ris) e um espelho
legível (fichamento.md).

O que o script preenche automaticamente (a partir de fonte confiável):
  - metadados bibliográficos (CrossRef)
  - referência ABNT NBR 6023:2018
  - resumo ORIGINAL do artigo, quando localizável no texto extraído
  - trechos CANDIDATOS a citação (resumo, conclusão) — extraídos do PDF

O que VOCÊ preenche depois de LER o artigo (campos marcados [PREENCHER]):
  - resumo com as suas palavras (evita plágio)
  - citações diretas: "trecho literal" (AUTOR, ano, p. X) — com a página real
  - citações indiretas: paráfrase sua (AUTOR, ano)
  - onde entra no trabalho / relação com o Farol-SS

Uso:  python3 04_gerar_fichamento.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import html
from lib_revisao import chamada_autor_data, referencia_abnt, ris_record

HERE = Path(__file__).parent
SEL = json.loads((HERE / "selecao.json").read_text(encoding="utf-8"))
TXT = HERE / "texto"


def bloco(texto: str, marcadores, limite=1400) -> str:
    """primeiro parágrafo após um dos marcadores (Resumo, Conclusão…)."""
    low = texto.lower()
    for m in marcadores:
        i = low.find(m)
        if i == -1:
            continue
        trecho = texto[i + len(m): i + len(m) + limite]
        trecho = re.split(r"\n\s*\n", trecho.strip(), maxsplit=1)[0]
        trecho = re.sub(r"\s+", " ", trecho).strip(" :.-–—")
        if len(trecho) > 120:
            return trecho[:limite]
    return ""


PREENCHER = "[PREENCHER APÓS LER O PDF]"
ris_out, md_out = [], ["# Fichamento — revisão para o SIPES 2026\n",
    "> Gerado por `04_gerar_fichamento.py`. Os campos [PREENCHER] são seus, "
    "escritos **com suas palavras** a partir da leitura do PDF. Trechos "
    "\"CANDIDATOS\" foram extraídos do arquivo e precisam ter a **página "
    "conferida** no PDF antes de virar citação direta.\n",
    "> Referências no padrão **ABNT NBR 6023:2018**; citações no texto no "
    "padrão **autor-data NBR 10520:2023**.\n"]

for n, (k, meta) in enumerate(SEL.items(), 1):
    item = meta["item"]
    ref = html.unescape(referencia_abnt(item)).replace("<b>", "").replace("</b>", "")
    tpath = TXT / f"{k}.txt"
    texto = tpath.read_text(encoding="utf-8", errors="ignore") if tpath.exists() else ""
    resumo_orig = bloco(texto, ["resumo\n", "resumo ", "abstract\n", "abstract "])
    conclusao = bloco(texto, ["considerações finais", "conclusão", "conclusões",
                              "conclusion", "final remarks"])
    tem_pdf = "sim" if texto else "NÃO — obter o PDF (Portal CAPES) e reprocessar"

    au = item.get("author") or [{}]
    ano = (item.get("issued", {}).get("date-parts") or [[""]])[0][0]
    autor_data, autor_texto = chamada_autor_data(item)

    n1 = [
        f"=== FICHA {n:02d} · {k} ===",
        f"Qualis (2017-2020): {meta['qualis']}   |   PDF extraído: {tem_pdf}",
        f"REFERÊNCIA (ABNT NBR 6023): {ref}",
        f"CHAMADA NO TEXTO (NBR 10520): {autor_data}  |  no texto: {autor_texto}",
        "",
        f"RESUMO ORIGINAL DO ARTIGO (do próprio artigo — não é o seu; resumir com suas palavras abaixo): {resumo_orig or '[não localizado — ver PDF]'}",
        "",
        f"RESUMO COM SUAS PALAVRAS (3-6 frases): {PREENCHER}",
        f"OBJETIVO DO ESTUDO: {PREENCHER}",
        f"MÉTODO / DADOS / PERÍODO: {PREENCHER}",
        f"PRINCIPAIS ACHADOS (com números): {PREENCHER}",
        "",
        f"TRECHO CANDIDATO 1 (conclusão, extraído — conferir página): "
        f"{conclusao or '[não localizado]'}",
        f"CITAÇÃO DIRETA 1 (ate 3 linhas, entre aspas, no corpo): \"[trecho literal]\" {autor_data[:-1]}, p. [X]).",
        f"CITAÇÃO DIRETA 2 (longa, +3 linhas → recuo 4 cm, fonte menor, sem aspas): {PREENCHER}",
        f"CITAÇÃO INDIRETA 1 (paráfrase sua): [ideia reescrita] {autor_data}.",
        f"CITAÇÃO INDIRETA 2: {PREENCHER}",
        "",
        f"CONCEITO/DEFINIÇÃO QUE O ARTIGO EMPRESTA AO TRABALHO: {PREENCHER}",
        f"RELAÇÃO COM O FAROL-SS (sustenta introdução/método/discussão? contrapõe?): {PREENCHER}",
        f"ONDE ENTRA NO PÔSTER: [ ] Introdução  [ ] Metodologia  [ ] Resultados/Discussão  [ ] Limitações",
    ]

    ris_out.append(ris_record(item, extra={
        "KW": ["fichamento SIPES 2026", f"Qualis {meta['qualis']}"],
        "N1": n1,
    }))

    md_out.append(f"\n## {n:02d}. {(item.get('title') or [''])[0]}\n")
    md_out.append(f"**Qualis {meta['qualis']}** · {meta['periodico']} · "
                  f"PDF: {tem_pdf}\n")
    md_out.append(f"**Referência (ABNT NBR 6023:2018):** {ref}\n")
    md_out.append(f"**Chamada no texto (NBR 10520:2023):** {autor_data} · no texto: {autor_texto}\n")
    md_out.append(f"**Resumo original (extraído — conferir):** "
                  f"{resumo_orig or '_não localizado_'}\n")
    md_out.append("| Campo | Conteúdo |\n|---|---|")
    for campo in ["Resumo com suas palavras", "Objetivo", "Método/dados",
                  "Principais achados", "Conceito emprestado ao trabalho",
                  "Relação com o Farol-SS", "Onde entra no pôster"]:
        md_out.append(f"| {campo} | {PREENCHER} |")
    md_out.append(f"\n**Trecho candidato (conclusão, extraído):** "
                  f"{conclusao or '_não localizado_'}\n")
    md_out.append(f'**Citação direta** (ate 3 linhas, aspas; +3 linhas: recuo 4 cm, '
                  f'fonte menor, sem aspas — conferir página): `"[trecho]" {autor_data[:-1]}, p. XX).`\n')
    md_out.append(f"**Citação indireta (paráfrase):** `[ideia reescrita com suas palavras] {autor_data}.`\n")

(HERE / "fichamento.ris").write_text("\n".join(ris_out), encoding="utf-8")
(HERE / "fichamento.md").write_text("\n".join(md_out), encoding="utf-8")
print(f"-> fichamento.ris  ({len(SEL)} fichas)")
print(f"-> fichamento.md")
faltam_pdf = [k for k, m in SEL.items() if not (TXT / f'{k}.txt').exists()]
if faltam_pdf:
    print(f"\n{len(faltam_pdf)} artigos ainda sem PDF/texto — completar e rodar 03 e 04 de novo:")
    for k in faltam_pdf:
        print(f"  - {k}  (DOI {SEL[k]['doi']})")

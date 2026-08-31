#!/usr/bin/env python3
"""05 — funde fichas_analiticas.yml (síntese redigida a partir dos PDFs) nos
campos analíticos do fichamento, regenerando fichamento.ris e fichamento.md.

Artigo com entrada em fichas_analiticas.yml -> ficha completa.
Artigo sem entrada (ex.: os 7 sem PDF) -> mantém o esqueleto [PREENCHER].

Uso:  python3 05_fichar_analitico.py
"""
from __future__ import annotations

import html
import json
import re
import textwrap
from pathlib import Path

import yaml

from lib_revisao import chamada_autor_data, referencia_abnt, ris_record

HERE = Path(__file__).parent
SEL = json.loads((HERE / "selecao.json").read_text(encoding="utf-8"))
ANA = yaml.safe_load((HERE / "fichas_analiticas.yml").read_text(encoding="utf-8")) or {}
TXT = HERE / "texto"
PREENCHER = "[PREENCHER APÓS LER O PDF]"


def w(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def q(s: str) -> str:
    """trecho literal sem aspas nas pontas (elas são adicionadas na formatação)."""
    return w(s).strip('"\u201c\u201d\u00ab\u00bb ')


ris_out, md = [], [
    "# Fichamento — revisão para o SIPES 2026\n",
    "> Referências: **ABNT NBR 6023:2018**. Chamada no texto: **autor-data "
    "NBR 10520:2023** (direta ≤ 3 linhas entre aspas com página; > 3 linhas em "
    "recuo de 4 cm, fonte menor, sem aspas).\n",
    "> `resumo` = redação própria a partir do texto completo do PDF. "
    "`citação direta` = trecho literal — **confira a página exata no PDF** "
    f"(o intervalo do artigo está indicado). {len(ANA)} de {len(SEL)} fichas "
    "analíticas preenchidas; as demais aguardam o PDF (ver RESULTADO.md).\n",
]

for n, (k, meta) in enumerate(SEL.items(), 1):
    item = meta["item"]
    ref = html.unescape(referencia_abnt(item)).replace("<b>", "").replace("</b>", "")
    dentro, no_texto = chamada_autor_data(item)
    tem_txt = (TXT / f"{k}.txt").exists()
    a = ANA.get(k)

    if a:
        tipo = a.get("tipo", "completa")
        rot = {"completa": "ficha completa (texto integral)",
               "parcial": "ficha parcial — redigida a partir do RESUMO publicado; "
                          "citação direta e página exigem o texto integral"}[tipo]
        n1 = [
            f"=== FICHA {n:02d} · {k}  ·  Qualis {meta['qualis']}  ·  {rot} ===",
            f"REFERÊNCIA (NBR 6023): {ref}",
            f"CHAMADA (NBR 10520): {dentro}  |  no texto: {no_texto}",
            "",
            f"RESUMO (redação própria): {w(a['resumo'])}",
            "",
            (f"CITAÇÃO DIRETA — trecho literal ({a.get('citacao_direta_local','conferir página')}):"
             if tipo == "completa" else
             f"CITAÇÃO DIRETA — do resumo publicado, CONFIRMAR no texto integral ({a.get('citacao_direta_local','')}):"),
            f'  "{q(a["citacao_direta"])}" {dentro[:-1]}, p. [conferir]).',
            "",
            f"CITAÇÃO INDIRETA (paráfrase própria): {w(a['citacao_indireta'])} {dentro}.",
            "",
            f"CONCEITO QUE EMPRESTA AO TRABALHO: {w(a['conceito'])}",
            f"RELAÇÃO COM O FAROL-SS: {w(a['relacao_farol'])}",
            f"ONDE ENTRA NO PÔSTER: {a['onde']}",
        ]
    else:
        n1 = [
            f"=== FICHA {n:02d} · {k}  ·  Qualis {meta['qualis']} ===",
            f"REFERÊNCIA (NBR 6023): {ref}",
            f"CHAMADA (NBR 10520): {dentro}  |  no texto: {no_texto}",
            f"PDF: {'texto disponível em texto/' if tem_txt else 'NÃO — obter no Portal CAPES (ver RESULTADO.md)'}",
            "",
            f"RESUMO (redação própria): {PREENCHER}",
            f"CITAÇÃO DIRETA: \"[trecho]\" {dentro[:-1]}, p. [X]).",
            f"CITAÇÃO INDIRETA: [paráfrase] {dentro}.",
            f"CONCEITO / RELAÇÃO COM O FAROL-SS / ONDE ENTRA: {PREENCHER}",
        ]

    ris_out.append(ris_record(item, extra={
        "KW": ["fichamento SIPES 2026", f"Qualis {meta['qualis']}",
               ("ficha completa" if a.get("tipo","completa")=="completa" else "ficha parcial") if a else "ficha pendente"],
        "N1": n1,
    }))

    # espelho markdown
    md.append(f"\n## {n:02d}. {html.unescape((item.get('title') or [''])[0])}\n")
    _st = ("ficha completa" if (a and a.get("tipo","completa")=="completa")
           else "ficha parcial (do resumo publicado)" if a else "ficha pendente (sem PDF)")
    md.append(f"**Qualis {meta['qualis']}** · {html.unescape(meta['periodico'])} · {_st}\n")
    md.append(f"**Referência (NBR 6023):** {ref}\n")
    md.append(f"**Chamada (NBR 10520):** {dentro} · no texto: {no_texto}\n")
    if a:
        md.append(f"**Resumo (redação própria):** {w(a['resumo'])}\n")
        _lbl = ("Citação direta" if a.get("tipo","completa")=="completa"
                else "Citação direta — do resumo publicado, CONFIRMAR no texto integral")
        md.append(f"**{_lbl}** ({a.get('citacao_direta_local','conferir página')}):\n\n"
                  f"> \"{q(a['citacao_direta'])}\" {dentro[:-1]}, p. [conferir]).\n")
        md.append(f"**Citação indireta:** {w(a['citacao_indireta'])} {dentro}.\n")
        md.append(f"**Conceito:** {w(a['conceito'])}  \n"
                  f"**Relação com o Farol-SS:** {w(a['relacao_farol'])}  \n"
                  f"**Onde entra:** {a['onde']}\n")
    else:
        md.append(f"_Ficha pendente — {PREENCHER} (obter o PDF, ver RESULTADO.md)._\n")

(HERE / "fichamento.ris").write_text("\n".join(ris_out), encoding="utf-8")
(HERE / "fichamento.md").write_text("\n".join(md), encoding="utf-8")
print(f"-> fichamento.ris e fichamento.md  ({sum(1 for k in SEL if k in ANA)}/{len(SEL)} fichas preenchidas)")
pend = [k for k in SEL if k not in ANA]
if pend:
    print("pendentes (adicionar a fichas_analiticas.yml após ler o PDF):")
    print(textwrap.fill(", ".join(pend), 90, initial_indent="  ", subsequent_indent="  "))

#!/usr/bin/env python3
"""01 — resolve as buscas e sementes de consulta.yml no CrossRef, filtra por
periódico Qualis A/B, e escreve referencias.ris + referencias.csv.

Uso:  python3 01_montar_ris.py
Saída: referencias.ris, referencias.csv, selecao.json
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import yaml

from lib_revisao import (
    cave_key,
    crossref_by_query,
    referencia_abnt,
    ris_record,
)

HERE = Path(__file__).parent
CFG = yaml.safe_load((HERE / "consulta.yml").read_text(encoding="utf-8"))
EMAIL = CFG["email"]
ALVO = 20
LIMITE = 22  # teto — sobra para os que não tiverem PDF de acesso aberto

issn_qualis: dict[str, str] = {}
issn_all: list[str] = []
for p in CFG["periodicos_qualis"]:
    for i in p["issn"]:
        issn_qualis[i] = p["qualis"]
        issn_all.append(i)


def qualis_de(item) -> str | None:
    for i in item.get("ISSN") or []:
        if i in issn_qualis:
            return issn_qualis[i]
    return None


EXCLUIR = set(CFG.get('excluir') or [])
selec: dict[str, dict] = {}
_titulos: set[str] = set()
_dois: set[str] = set()


def _norm_tit(t: str) -> str:
    import re as _re

    return _re.sub(r"[^a-z0-9]+", "", (t or "").lower())[:55]


def _doi_base(doi: str) -> str:
    # remove só o sufixo de tradução do SciELO (ex.: 10.1590/xxxx.2 / .en / .pt)
    import re as _re

    return _re.sub(r"\.(?:\d{1,2}|en|pt|es)$", "", (doi or "").lower())


def considerar(item, origem) -> bool:
    if not item or not item.get("DOI") or not item.get("title"):
        return False
    q = qualis_de(item)
    if not q:
        return False
    nt = _norm_tit(item["title"][0])
    db = _doi_base(item["DOI"])
    if nt in _titulos or db in _dois:
        return False  # duplicata (inclui versão bilíngue PT/EN)
    k = cave_key(item)
    if k in selec or k in EXCLUIR:
        return False
    selec[k] = {"item": item, "qualis": q, "origem": origem}
    _titulos.add(nt)
    _dois.add(db)
    print(f"  + [{q}] {k}  ({(item.get('container-title') or ['?'])[0]})")
    return True


print("== sementes (prioridade — fundamentais/internacionais) ==")
for s in CFG["sementes"]:
    if len(selec) >= LIMITE:
        break
    hits = crossref_by_query(s, EMAIL, rows=5)  # sem filtro de ISSN; Qualis é exigido em considerar()
    if not any(considerar(it, f"semente:{s[:40]}") for it in hits):
        print(f"  ! não incluído: {s[:55]}  (top: "
              f"{(hits[0].get('container-title') or ['?'])[0][:30] if hits else 'nada'})")

print("\n== buscas por tema (CrossRef, restrito aos ISSN Qualis A/B) ==")
for b in CFG["buscas"]:
    if len(selec) >= LIMITE:
        break
    print(f"- {b['tema']}")
    hits = crossref_by_query(b["query"], EMAIL, rows=b.get("n", 5) + 6,
                             issn=issn_all, de=b.get("de"), ate=b.get("ate"))
    got = 0
    for it in hits:
        if got >= b.get("n", 5) or len(selec) >= LIMITE:
            break
        if considerar(it, f"tema:{b['tema']}"):
            got += 1

itens = list(selec.items())
print(f"\n== {len(itens)} artigos Qualis A/B selecionados (alvo {ALVO}) ==")
if len(itens) < ALVO:
    print("  AVISO: abaixo do alvo. Amplie 'buscas' em consulta.yml (mais termos/anos/n).")

# saídas
ris = HERE / "referencias.ris"
with ris.open("w", encoding="utf-8") as f:
    for k, rec in itens:
        f.write(ris_record(rec["item"], extra={
            "KW": ["revisão SIPES 2026", f"Qualis {rec['qualis']}"],
            "N1": [f"chave: {k}", f"origem: {rec['origem']}",
                   f"Qualis (2017-2020): {rec['qualis']}",
                   f"referência ABNT: {referencia_abnt(rec['item'])}"],
        }))
print(f"  -> {ris.name}")

with (HERE / "referencias.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["chave", "qualis", "ano", "periodico", "titulo", "doi", "origem"])
    for k, rec in itens:
        it = rec["item"]
        w.writerow([k, rec["qualis"],
                    (it.get("issued", {}).get("date-parts") or [[""]])[0][0],
                    (it.get("container-title") or [""])[0],
                    (it.get("title") or [""])[0], it.get("DOI"), rec["origem"]])
print(f"  -> referencias.csv")

(HERE / "selecao.json").write_text(
    json.dumps({k: {"doi": v["item"]["DOI"], "qualis": v["qualis"],
                    "titulo": v["item"]["title"][0],
                    "periodico": (v["item"].get("container-title") or [""])[0],
                    "item": v["item"]}
                for k, v in itens}, ensure_ascii=False, indent=1),
    encoding="utf-8")
print(f"  -> selecao.json  ({len(itens)} registros)")

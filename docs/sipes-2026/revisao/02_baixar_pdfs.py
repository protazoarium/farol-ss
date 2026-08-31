#!/usr/bin/env python3
"""02 — baixa os PDFs de acesso aberto dos artigos de selecao.json para pdfs/.

Só baixa o que estiver legalmente em acesso aberto (Unpaywall / SciELO / PMC).
Artigos sem versão OA ou bloqueados por antibot ficam em pdfs/_faltantes.txt
para você obter pelo Portal de Periódicos CAPES / biblioteca da instituição.

Uso:  python3 02_baixar_pdfs.py
"""
from __future__ import annotations

import json
from pathlib import Path

import requests
import yaml

from lib_revisao import oa_pdf_candidates

HERE = Path(__file__).parent
EMAIL = yaml.safe_load((HERE / "consulta.yml").read_text())["email"]
SEL = json.loads((HERE / "selecao.json").read_text(encoding="utf-8"))
PDFS = HERE / "pdfs"
PDFS.mkdir(exist_ok=True)

BROWSER = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "application/pdf,text/html;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}

ok, faltam = [], []
sess = requests.Session()
sess.headers.update(BROWSER)

for k, meta in SEL.items():
    dest = PDFS / f"{k}.pdf"
    if dest.exists() and dest.stat().st_size > 20_000:
        print(f"= {k} (já baixado)")
        ok.append(k)
        continue
    cands = oa_pdf_candidates(meta["doi"], EMAIL)
    if not cands:
        print(f"! {k} — sem versão OA (DOI {meta['doi']})")
        faltam.append(f"{k}\t{meta['doi']}\tsem OA — Portal CAPES")
        continue
    baixou = False
    for url, lic in cands:
        try:
            r = sess.get(url, timeout=60, allow_redirects=True)
            ct = r.headers.get("content-type", "")
            if r.status_code == 200 and (b"%PDF" in r.content[:2048] or "application/pdf" in ct):
                dest.write_bytes(r.content)
                print(f"+ {k}  ({len(r.content)//1024} kB, {lic or 'lic?'})")
                ok.append(k)
                baixou = True
                break
        except requests.RequestException:
            pass
    if not baixou:
        print(f"! {k} — nenhuma candidata retornou PDF ({len(cands)} tentadas)")
        faltam.append(f"{k}\t{meta['doi']}\thttps://doi.org/{meta['doi']}")

(PDFS / "_faltantes.txt").write_text(
    "chave\tDOI\turl/observação\n" + "\n".join(faltam), encoding="utf-8")
print(f"\n{len(ok)} PDFs em pdfs/  ·  {len(faltam)} faltando (ver pdfs/_faltantes.txt)")

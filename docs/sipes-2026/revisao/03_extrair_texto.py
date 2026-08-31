#!/usr/bin/env python3
"""03 — extrai o texto completo de cada PDF de pdfs/ para texto/{chave}.txt,
com marcador «[[página N]]» no início de cada página (para citar p. N)."""
from __future__ import annotations

from pathlib import Path

import pymupdf

HERE = Path(__file__).parent
PDFS = HERE / "pdfs"
TXT = HERE / "texto"
TXT.mkdir(exist_ok=True)

rows = []
for pdf in sorted(PDFS.glob("*.pdf")):
    try:
        doc = pymupdf.open(pdf)
        partes = [f"\n[[página {i + 1}]]\n" + p.get_text("text") for i, p in enumerate(doc)]
        texto = "".join(partes).strip()
        (TXT / f"{pdf.stem}.txt").write_text(texto, encoding="utf-8")
        rows.append((pdf.stem, doc.page_count, len(texto)))
        print(f"+ {pdf.stem}: {doc.page_count} pág., {len(texto):,} caracteres")
        doc.close()
    except Exception as e:  # noqa: BLE001
        print(f"! {pdf.stem}: {type(e).__name__} — {e}")

print(f"\n{len(rows)} textos em texto/")
for s in [r for r in rows if r[2] < 3000]:
    print(f"  revisar (pouco texto, talvez PDF de imagem): {s[0]} ({s[2]})")

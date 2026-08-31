#!/usr/bin/env python3
"""03 — extrai o texto completo de cada PDF de pdfs/ para texto/{chave}.txt.

Uso:  python3 03_extrair_texto.py
"""
from __future__ import annotations

from pathlib import Path

import pymupdf as fitz  # PyMuPDF

HERE = Path(__file__).parent
PDFS = HERE / "pdfs"
TXT = HERE / "texto"
TXT.mkdir(exist_ok=True)

rows = []
for pdf in sorted(PDFS.glob("*.pdf")):
    try:
        doc = fitz.open(pdf)
        partes = [p.get_text("text") for p in doc]
        texto = "\n".join(partes).strip()
        (TXT / f"{pdf.stem}.txt").write_text(texto, encoding="utf-8")
        rows.append((pdf.stem, doc.page_count, len(texto)))
        print(f"+ {pdf.stem}: {doc.page_count} pág., {len(texto):,} caracteres")
        doc.close()
    except Exception as e:  # noqa: BLE001
        print(f"! {pdf.stem}: {type(e).__name__} — {e}")

print(f"\n{len(rows)} textos em texto/")
suspeitos = [r for r in rows if r[2] < 3000]
if suspeitos:
    print("  revisar (pouco texto — pode ser PDF de imagem, precisa OCR):")
    for s in suspeitos:
        print(f"   - {s[0]} ({s[2]} caracteres)")

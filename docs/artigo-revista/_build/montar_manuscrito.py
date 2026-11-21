"""Monta 03-manuscrito.docx: injeta as referências (de refs.js) e chama o pandoc.

Uso (a partir de docs/artigo-revista/): node -e para dump de refs -> JSON; este script
lê o JSON e o .md. Ver comando no README do pacote.
"""
import json, re, subprocess, sys, pathlib
base = pathlib.Path(__file__).resolve().parent.parent
md = (base / "03-manuscrito.md").read_text(encoding="utf-8")
refs = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
txt = sorted((r["ref"] for r in refs), key=lambda s: re.sub(r"[^A-ZÀ-Ý]", "", s.upper()))
out = "\n\n".join(txt)
(base / "_build" / "_manuscrito_com_refs.md").write_text(md.replace("<!--REFS-->", out), encoding="utf-8")
subprocess.run(["pandoc", str(base / "_build" / "_manuscrito_com_refs.md"), "-o", str(base / "03-manuscrito.docx"),
                "--from", "markdown+pipe_tables"], check=True)
print("ok")

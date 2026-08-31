"""Utilidades da revisão: consulta CrossRef/Unpaywall, chave estável, RIS,
referência ABNT (NBR 6023:2018)."""
from __future__ import annotations

import html
import re
import time
import unicodedata

import requests

UA = "farol-ss-revisao/1.0 (https://github.com/protazoarium/farol-ss; mailto:{email})"


def _get(url, params=None, email="", tries=3):
    headers = {"User-Agent": UA.format(email=email or "anon@example.org")}
    params = dict(params or {})
    if "api.crossref.org" in url:
        params.setdefault("mailto", email or "anon@example.org")  # pool "polite" = rápido
    for i in range(tries):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=25)
            if r.status_code in (200, 400, 404, 422):
                return r
        except requests.RequestException:
            pass
        time.sleep(2 * (i + 1))
    return None


def slug(text, n=48):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:n]


def cave_key(item: dict) -> str:
    """chave estável: primeiroautor_ano_palavra"""
    au = item.get("author") or [{}]
    fam = slug((au[0].get("family") or au[0].get("name") or "anon"), 20)
    year = str((item.get("issued", {}).get("date-parts") or [[0]])[0][0] or "0000")
    tit = (item.get("title") or ["sem-titulo"])[0]
    w = next((slug(x, 14) for x in re.split(r"\W+", tit) if len(x) > 4), "art")
    return f"{fam}_{year}_{w}"


def crossref_by_query(query, email, rows=3, issn=None, de=None, ate=None):
    params = {"query.bibliographic": query, "rows": rows}
    filt = ["type:journal-article"]
    if issn:  # OR de ISSN = repetir a chave: issn:A,issn:B,...
        vals = issn if isinstance(issn, (list, tuple)) else [issn]
        filt += [f"issn:{v}" for v in vals]
    if de:
        filt.append(f"from-pub-date:{de}-01-01")
    if ate:
        filt.append(f"until-pub-date:{ate}-12-31")
    params["filter"] = ",".join(filt)
    r = _get("https://api.crossref.org/works", params, email)
    if not r or r.status_code != 200:
        return []
    try:
        return r.json().get("message", {}).get("items", [])
    except ValueError:
        return []


def crossref_by_doi(doi, email):
    r = _get(f"https://api.crossref.org/works/{doi}", email=email)
    if not r or r.status_code != 200:
        return None
    return r.json().get("message")


def unpaywall(doi, email):
    r = _get(f"https://api.unpaywall.org/v2/{doi}", {"email": email}, email)
    if not r or r.status_code != 200:
        return None
    try:
        return r.json()
    except ValueError:
        return None


def oa_pdf_candidates(doi, email):
    """lista de (url, licença) candidatas, da melhor para a pior."""
    out = []
    d = unpaywall(doi, email)
    locs = []
    if d:
        for k in ("best_oa_location", "first_oa_location"):
            if d.get(k):
                locs.append(d[k])
        locs += d.get("oa_locations") or []
    for loc in locs:
        lic = loc.get("license")
        if loc.get("url_for_pdf"):
            out.append((loc["url_for_pdf"], lic))
        u = loc.get("url") or ""
        if "scielo.br/j/" in u:
            base = u.split("?")[0].rstrip("/")
            out.append((f"{base}/?format=pdf&lang=pt", lic))
            out.append((f"{base}/?format=pdf&lang=en", lic))
        if "ncbi.nlm.nih.gov/pmc/articles/" in u or "/pmc/" in u:
            pmcid = re.search(r"(PMC\d+)", u)
            if pmcid:
                out.append((f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid.group(1)}/pdf/", lic))
    # ESS (scielo.iec / scielosp) a partir do DOI 10.5123/xxxx
    m = re.match(r"10\.5123/(s\d{4}-\d{8})(\d{10})", doi.lower().replace("-", ""))
    if doi.lower().startswith("10.5123/"):
        out.append((f"https://doi.org/{doi}", None))  # o redirecionador às vezes leva ao PDF
    # dedup preservando ordem
    seen, uniq = set(), []
    for u, lic in out:
        if u not in seen:
            seen.add(u)
            uniq.append((u, lic))
    return uniq


def oa_pdf_url(doi, email):  # compat
    c = oa_pdf_candidates(doi, email)
    return (c[0] if c else (None, None))


# ── formatação ─────────────────────────────────────────────────────────
_MESES = {}


def _authors_abnt(item):
    out = []
    for a in item.get("author") or []:
        fam = (a.get("family") or a.get("name") or "").strip()
        giv = (a.get("given") or "").strip()
        if not fam:
            continue
        ini = " ".join(f"{p[0]}." for p in re.split(r"[\s.-]+", giv) if p)
        out.append(f"{fam.upper()}, {ini}".strip().rstrip(","))
    if not out:
        return "[AUTOR NÃO IDENTIFICADO]"
    if len(out) > 3:
        return out[0] + " et al."
    return "; ".join(out)


def chamada_autor_data(item: dict, ano_fora=False):
    """Citação no sistema autor-data (NBR 10520:2023).
    Retorna (dentro_dos_parenteses, no_texto). ano_fora não usado; conveniência.
    1 autor: (SOBRENOME, ano) · 2-3: (A; B; C, ano) · 4+: (A et al., ano)."""
    au = item.get("author") or []
    fams = [(a.get("family") or a.get("name") or "").strip() for a in au]
    fams = [f for f in fams if f]
    ano = (item.get("issued", {}).get("date-parts") or [[""]])[0][0] or "s.d."
    if not fams:
        return f"([AUTOR], {ano})", f"[AUTOR] ({ano})"
    if len(fams) > 3:
        dentro = f"{fams[0].upper()} et al., {ano}"
        texto = f"{fams[0].title()} et al. ({ano})"
    else:
        dentro = "; ".join(f.upper() for f in fams) + f", {ano}"
        texto = "; ".join(f.title() for f in fams[:-1])
        texto = (texto + " e " if texto else "") + fams[-1].title() + f" ({ano})"
    return f"({dentro})", texto


def referencia_abnt(item: dict) -> str:
    """NBR 6023:2018 — artigo de periódico."""
    aut = _authors_abnt(item)
    tit = html.unescape((item.get("title") or ["[sem título]"])[0]).strip().rstrip(".")
    per = html.unescape((item.get("container-title") or ["[periódico]"])[0]).strip()
    year = str((item.get("issued", {}).get("date-parts") or [[""]])[0][0] or "s.d.")
    vol = item.get("volume")
    nph = item.get("issue")
    pag = item.get("page")
    doi = item.get("DOI")
    ref = f"{aut} {tit}. <b>{per}</b>, "
    if vol:
        ref += f"v. {vol}, "
    if nph:
        ref += f"n. {nph}, "
    if pag:
        ref += f"p. {pag}, "
    ref += f"{year}."
    if doi:
        ref += f" DOI: https://doi.org/{doi}. Acesso em: [DATA]."
    return re.sub(r"\s+,", ",", ref)


def ris_record(item: dict, extra: dict | None = None) -> str:
    """Registro RIS. extra: dict de campos adicionais (ex.: N1 lista, KW lista)."""
    L = []
    ty = {"journal-article": "JOUR", "proceedings-article": "CPAPER",
          "book-chapter": "CHAP", "book": "BOOK"}.get(item.get("type"), "JOUR")
    L.append(f"TY  - {ty}")
    for a in item.get("author") or []:
        fam = (a.get("family") or a.get("name") or "").strip()
        giv = (a.get("given") or "").strip()
        if fam:
            L.append(f"AU  - {fam}, {giv}".rstrip(", "))
    if item.get("title"):
        L.append(f"TI  - {html.unescape(item['title'][0])}")
    if item.get("container-title"):
        ct = html.unescape(item["container-title"][0])
        L.append(f"JO  - {ct}")
        L.append(f"JF  - {ct}")
    yr = (item.get("issued", {}).get("date-parts") or [[""]])[0][0]
    if yr:
        L.append(f"PY  - {yr}")
    if item.get("volume"):
        L.append(f"VL  - {item['volume']}")
    if item.get("issue"):
        L.append(f"IS  - {item['issue']}")
    if item.get("page"):
        pg = str(item["page"]).split("-")
        L.append(f"SP  - {pg[0]}")
        if len(pg) > 1:
            L.append(f"EP  - {pg[1]}")
    for isn in item.get("ISSN") or []:
        L.append(f"SN  - {isn}")
    if item.get("DOI"):
        L.append(f"DO  - {item['DOI']}")
        L.append(f"UR  - https://doi.org/{item['DOI']}")
    ab = item.get("abstract")
    if ab:
        ab = re.sub(r"<[^>]+>", "", ab).replace("\n", " ").strip()
        L.append(f"AB  - {ab}")
    for k, vals in (extra or {}).items():
        for v in (vals if isinstance(vals, list) else [vals]):
            L.append(f"{k}  - {v}")
    L.append("ER  - ")
    return "\n".join(L) + "\n"

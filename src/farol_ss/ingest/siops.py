"""Ingestão do SIOPS — camada L2 (execução própria municipal em saúde).

O SIOPS não tem API REST. A série histórica de indicadores municipais vive no
TabNet legado (`siops-asp.datasus.gov.br`), um CGI que responde a um POST de
formulário e devolve HTML. Dois detalhes que fizeram a diferença:

1. **Encoding**: o CGI é ISO-8859-1. Os valores acentuados do formulário
   (`Municípios`, `D.R.Próprios_em_Saúde/Hab`) precisam ser URL-encodados em
   latin-1 — mandar UTF-8 devolve "Tabela de conversao nao encontrada".
2. **`Coluna`**: com um único arquivo-ano, `Coluna` tem de ser
   `--Não-Ativa--`; `Ano` só é coluna válida com vários anos selecionados.
   Aqui pedimos um ano por requisição e montamos a série.

Indicador coletado: **`D.R.Próprios_em_Saúde/Hab`** — despesa com recursos
próprios do município em saúde, por habitante, em R$ correntes do ano. É a
definição operacional da camada L2 do IEAS (execução própria, distinta do
repasse federal L1). Também guardamos `%R.Próprios_em_Saúde-EC_29`
(percentual da receita própria aplicado em saúde, piso constitucional de 15%).
"""

from __future__ import annotations

import re
import urllib.parse

import pandas as pd

from farol_ss import config
from farol_ss.ingest.base import Fetcher, Proveniencia, _agora, registrar, sha256
from farol_ss.io import duck
from farol_ss.io import municipios as M

_URL = "http://siops-asp.datasus.gov.br/cgi/tabcgi.exe?siops/serhist/MUNICIPIO/indicPE.def"

# indicador do formulário → nome da coluna no silver
_INDICADORES = {
    "D.R.Próprios_em_Saúde/Hab": "l2_rec_proprios_per_capita",
    "3.2_%R.Próprios_em_Saúde-EC_29": "pct_receita_propria_saude",
}


def _enc(s: str) -> str:
    return urllib.parse.quote(s.encode("latin-1"))


def _num_br(texto: str) -> float | None:
    """'1.000,88' → 1000.88 ; '-' / '' → None."""
    t = texto.strip().replace(".", "").replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def _tabular(f: Fetcher, indicador: str, ano: int) -> pd.DataFrame:
    """Um POST ao TabNet: um indicador, um ano, todos os municípios de PE."""
    arquivo = f"indmun{ano % 100:02d}.dbf"
    campos = [
        ("Linha", "Municípios"),
        ("Coluna", "--Não-Ativa--"),
        ("Incremento", indicador),
        ("Arquivos", arquivo),
        ("SMunicípio", "TODAS_AS_CATEGORIAS__"),
        ("formato", "table"),
        ("mostre", "Mostra"),
    ]
    body = "&".join(f"{_enc(k)}={_enc(v)}" for k, v in campos)
    r = f.client.post(
        _URL, content=body, headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    r.raise_for_status()
    html = r.content.decode("latin-1")
    if "conversao nao encontrada" in html:
        raise RuntimeError(f"TabNet recusou o indicador {indicador!r} para {ano}")

    # a tabela do TabNet: <TH ALIGN=LEFT>NNNNNN Nome ... <TD>valor
    pares = re.findall(r"<TH ALIGN=LEFT>\s*(\d{6})\s[^<]*<TD>([^<]+)", html, re.IGNORECASE)
    linhas = []
    for cod6, valor in pares:
        cod_ibge = M.resolve_por_codigo(pd.Series([cod6])).iloc[0]
        if pd.isna(cod_ibge):
            continue
        linhas.append({"cod_ibge": cod_ibge, "ano": ano, "valor": _num_br(valor)})
    return pd.DataFrame(linhas)


def ingerir_siops() -> pd.DataFrame:
    config.ensure_dirs()
    anos = config.anos()
    por_indicador: dict[str, pd.DataFrame] = {}

    with Fetcher("siops") as f:
        for indicador, coluna in _INDICADORES.items():
            partes = []
            for ano in anos:
                try:
                    df = _tabular(f, indicador, ano)
                except Exception as e:  # noqa: BLE001 — ano ausente não derruba a série
                    print(f"    ⚠ SIOPS {coluna} {ano}: {type(e).__name__} {str(e)[:60]}")
                    continue
                if not df.empty:
                    partes.append(df.rename(columns={"valor": coluna}))
                    print(f"    ✓ SIOPS {coluna} {ano}: {len(df)} municípios")
            if partes:
                por_indicador[coluna] = pd.concat(partes, ignore_index=True)

    if not por_indicador:
        raise RuntimeError("SIOPS: nenhuma tabulação retornou dado.")

    out = None
    for df in por_indicador.values():
        out = df if out is None else out.merge(df, on=["cod_ibge", "ano"], how="outer")

    path = duck.write_silver(out, "siops")
    registrar(
        Proveniencia(
            fonte="siops",
            url=_URL,
            coletado_em=_agora(),
            arquivo=str(path.relative_to(config.ROOT)),
            sha256=sha256(out.to_csv(index=False).encode()),
            bytes=out.memory_usage(deep=True).sum().item(),
            linhas=len(out),
            observacao="TabNet legado (POST de formulário); indicador D.R.Próprios_em_Saúde/Hab",
            extra={
                "municipios": out["cod_ibge"].nunique(),
                "anos": sorted(out["ano"].unique().tolist()),
            },
        )
    )
    print(f"  ✓ siops: {len(out)} linhas, {out['cod_ibge'].nunique()} municípios")
    return out


def rodar() -> None:
    ingerir_siops()

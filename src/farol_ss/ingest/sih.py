"""Ingestão do SIH-SUS (internações hospitalares) via PySUS — subíndice de
internações por doenças relacionadas a saneamento ambiental inadequado (DRSAI).

Contexto histórico: o *spike* original (`docs/spike-fontes.md`) concluiu que
"nenhum código de grupo do SIH retorna dado utilizável" — só o grupo `SP`
(serviços profissionais), sem `MUNIC_RES` nem `DIAG_PRINC`. Isso estava
**errado**: a chamada `pysus.sih("PE", ano, mes, group="RD")` baixa o grupo
**RD (AIH Reduzida)**, que traz `MUNIC_RES` (185/185 municípios de PE),
`DIAG_PRINC` (CID-10) e `ANO_CMPT`, num arquivo pequeno (~2,7 MB/mês para PE).
O peso de internações do eixo epidemiológico, que fora redistribuído para
arboviroses e veiculação hídrica em `conf/ieas.yml`, volta com isto.

Métrica: contagem de AIH cujo `DIAG_PRINC` cai no grupo `veiculacao_hidrica`
de `seeds/cid_saneamento.csv` (o clássico indicador **DRSAI/ISA** — diarreias,
hepatite A, leptospirose, esquistossomose, helmintíases, febres tifoides).
Atribuída ao município de **residência** (`MUNIC_RES`), coerente com o SINAN.

Memória contida, como em `ingest/sinan.py`: `pysus.sih(...)` sem
`as_dataframe` devolve caminhos de Parquet já em disco; o filtro por UF e a
agregação são feitos com DuckDB antes de tocar pandas.
"""

from __future__ import annotations

import csv

import duckdb
import pandas as pd

from farol_ss import config
from farol_ss.ingest.base import Proveniencia, _agora, registrar, sha256
from farol_ss.io import duck
from farol_ss.io import municipios as M

_GRUPO = "RD"  # AIH Reduzida — tem MUNIC_RES + DIAG_PRINC


def _cids_drsai() -> set[str]:
    """CID-10 (sem ponto) do grupo veiculação hídrica de seeds/cid_saneamento.csv.

    O SIH grava `DIAG_PRINC` como código de 3 ou 4 caracteres sem ponto
    ('A090', 'B15', 'A928'). O seed mistura 3 e 4 caracteres — devolvemos o
    conjunto como está e o casamento (`_e_drsai`) testa o código cheio e o
    prefixo de 3.
    """
    caminho = config.SEEDS / "cid_saneamento.csv"
    with open(caminho, encoding="utf-8") as f:
        return {
            linha["cid10"].replace(".", "").strip().upper()
            for linha in csv.DictReader(f)
            if linha["grupo"] == "veiculacao_hidrica"
        }


def _e_drsai(diag: pd.Series, cids: set[str]) -> pd.Series:
    d = diag.astype(str).str.replace(".", "", regex=False).str.upper().str.strip()
    return d.isin(cids) | d.str[:3].isin(cids)


def _filtrar_pe(paths: list[str], ano: int, cids: set[str]) -> pd.DataFrame:
    """Conta AIH totais e DRSAI por município de residência de PE, num ano."""
    lista = ", ".join(f"'{p}'" for p in paths)
    con = duckdb.connect()
    con.execute("SET enable_progress_bar = false")
    df = con.execute(
        f"""
        SELECT CAST(MUNIC_RES AS VARCHAR) AS cod_bruto,
               CAST(DIAG_PRINC AS VARCHAR) AS diag
        FROM read_parquet([{lista}], union_by_name=true)
        WHERE substr(CAST(MUNIC_RES AS VARCHAR), 1, 2) = '26'
        """
    ).df()
    con.close()

    df["cod_ibge"] = M.resolve_por_codigo(df["cod_bruto"])
    df = df.dropna(subset=["cod_ibge"])
    if df.empty:
        return pd.DataFrame(columns=["cod_ibge", "ano", "internacoes_drsai", "internacoes_total"])

    df["_drsai"] = _e_drsai(df["diag"], cids)
    g = df.groupby("cod_ibge").agg(
        internacoes_total=("diag", "size"),
        internacoes_drsai=("_drsai", "sum"),
    )
    g = g.reset_index()
    g["ano"] = ano
    return g[["cod_ibge", "ano", "internacoes_drsai", "internacoes_total"]]


def ingerir_sih() -> pd.DataFrame:
    config.preparar_pysus()  # antes de import pysus
    import pysus

    config.ensure_dirs()
    duck.exigir_espaco(minimo_gb=2.0)
    cids = _cids_drsai()

    partes: list[pd.DataFrame] = []
    for ano in config.anos():
        try:
            paths = pysus.sih("PE", ano, list(range(1, 13)), group=_GRUPO)
        except Exception as e:  # noqa: BLE001 — DATASUS instável não derruba a ingestão
            print(f"  ✗ SIH {ano}: {type(e).__name__} {str(e)[:80]}")
            continue
        paths = [p for p in paths if p and p.endswith(".parquet")]
        if not paths:
            print(f"  · SIH {ano}: nenhum arquivo")
            continue
        parte = _filtrar_pe(paths, ano, cids)
        if parte.empty:
            print(f"  · SIH {ano}: 0 internações em PE")
            continue
        partes.append(parte)
        print(
            f"  ✓ SIH {ano}: {int(parte['internacoes_drsai'].sum())} internações DRSAI "
            f"/ {int(parte['internacoes_total'].sum())} totais em {parte['cod_ibge'].nunique()} municípios"
        )

    if not partes:
        raise RuntimeError("SIH: nenhum ano retornou dados")

    df = pd.concat(partes, ignore_index=True)
    df["internacoes_drsai"] = df["internacoes_drsai"].astype(int)
    df["internacoes_total"] = df["internacoes_total"].astype(int)

    path = duck.write_silver(df, "sih")
    registrar(
        Proveniencia(
            fonte="sih",
            url=f'pysus.sih("PE", {{ano}}, 1..12, group="{_GRUPO}")',
            coletado_em=_agora(),
            arquivo=str(path.relative_to(config.ROOT)),
            sha256=sha256(df.to_csv(index=False).encode()),
            bytes=df.memory_usage(deep=True).sum().item(),
            linhas=len(df),
            observacao=(
                "AIH Reduzida (grupo RD). internacoes_drsai = AIH cujo DIAG_PRINC "
                "está no grupo veiculação hídrica de seeds/cid_saneamento.csv "
                "(indicador DRSAI/ISA). Atribuída ao município de residência."
            ),
            extra={
                "municipios": df["cod_ibge"].nunique(),
                "anos": sorted(df["ano"].unique().tolist()),
            },
        )
    )
    print(f"  ✓ sih: {len(df)} município-anos, {df['cod_ibge'].nunique()} municípios")
    return df


def rodar() -> None:
    ingerir_sih()

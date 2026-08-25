"""Consolida os arquivos sinan_<agravo>_<ano>.parquet em uma única tabela.

A ingestão grava um arquivo por (agravo, ano) — conveniente para retomar após
falha e para auditar proveniência por fonte, mas inútil para join direto no
gold. Este módulo concatena tudo em `silver/epidemiologia.parquet`, no grão
(cod_ibge, ano, agravo).
"""

from __future__ import annotations

import re

import pandas as pd

from farol_ss import config
from farol_ss.io import duck

_PADRAO_ARQUIVO = re.compile(r"^sinan_([a-z]+)_(\d{4})\.parquet$")


def consolidar() -> pd.DataFrame:
    arquivos = sorted(config.SILVER.glob("sinan_*.parquet"))
    if not arquivos:
        raise FileNotFoundError(
            "Nenhum data/silver/sinan_*.parquet encontrado — rode `make ingest` primeiro."
        )

    partes = []
    for path in arquivos:
        m = _PADRAO_ARQUIVO.match(path.name)
        if not m:
            continue
        agravo = m.group(1).upper()
        df = pd.read_parquet(path)
        df["agravo"] = agravo
        partes.append(df)

    out = pd.concat(partes, ignore_index=True)
    # casos_confirmados só existe quando a doença tem CLASSI_FIN no SINAN
    if "casos_confirmados" not in out.columns:
        out["casos_confirmados"] = pd.NA
    return out[["cod_ibge", "ano", "agravo", "casos", "casos_confirmados"]]


def rodar() -> None:
    df = consolidar()
    duck.write_silver(df, "epidemiologia")
    print(f"  ✓ epidemiologia: {len(df)} linhas, {df.agravo.nunique()} agravos")

"""Consolida arquivos pncp_<modalidade>_<ano>.parquet em uma tabela única.

A ingestão grava um arquivo por (modalidade, ano) para preservar proveniência
e permitir retoma após falha. Este módulo consolida tudo em
`silver/pncp.parquet`, no grão (cod_ibge, ano, modalidade).
"""

from __future__ import annotations

import re

import pandas as pd

from farol_ss import config
from farol_ss.io import duck

_PADRAO_ARQUIVO = re.compile(r"^pncp_(\d+)_(\d{4})\.parquet$")


def consolidar() -> pd.DataFrame:
    """Lê todos os pncp_*.parquet, consolida em uma tabela única."""
    arquivos = sorted(config.SILVER.glob("pncp_*.parquet"))
    if not arquivos:
        return pd.DataFrame(
            columns=[
                "cod_ibge",
                "ano",
                "modalidade_id",
                "modalidade_nome",
                "numero_controle_pncp",
                "objeto_compra",
                "valor_total_homologado",
                "valor_total_estimado",
                "data_publicacao_pncp",
                "situacao_compra_nome",
            ]
        )

    partes = []
    for path in arquivos:
        m = _PADRAO_ARQUIVO.match(path.name)
        if not m:
            continue
        df = pd.read_parquet(path)
        partes.append(df)

    if not partes:
        return pd.DataFrame(
            columns=[
                "cod_ibge",
                "ano",
                "modalidade_id",
                "modalidade_nome",
                "numero_controle_pncp",
                "objeto_compra",
                "valor_total_homologado",
                "valor_total_estimado",
                "data_publicacao_pncp",
                "situacao_compra_nome",
            ]
        )

    out = pd.concat(partes, ignore_index=True)
    # Garantir tipos
    out["valor_total_homologado"] = pd.to_numeric(out["valor_total_homologado"], errors="coerce")
    out["valor_total_estimado"] = pd.to_numeric(out["valor_total_estimado"], errors="coerce")
    return out


def rodar() -> None:
    df = consolidar()
    duck.write_silver(df, "pncp")
    print(f"  ✓ pncp: {len(df)} linhas, {df['cod_ibge'].nunique()} municípios")

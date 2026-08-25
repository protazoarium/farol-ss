"""Acesso a dados: DuckDB sobre Parquet, sem servidor de banco.

O grão canônico do projeto é (cod_ibge, ano). Toda escrita em silver/gold
passa por aqui para que a convenção de nomes e o formato fiquem num lugar só.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from farol_ss import config


def connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(database=":memory:")
    con.execute("SET enable_progress_bar = false")
    return con


def write(df: pd.DataFrame, layer: Path, name: str) -> Path:
    """Grava um DataFrame como Parquet na camada indicada."""
    layer.mkdir(parents=True, exist_ok=True)
    path = layer / f"{name}.parquet"
    df.to_parquet(path, index=False, compression="zstd")
    return path


def write_silver(df: pd.DataFrame, name: str) -> Path:
    return write(df, config.SILVER, name)


def write_gold(df: pd.DataFrame, name: str) -> Path:
    return write(df, config.GOLD, name)


def read(layer: Path, name: str) -> pd.DataFrame:
    path = layer / f"{name}.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} não existe. Rode as etapas anteriores do pipeline (make all)."
        )
    return pd.read_parquet(path)


def read_silver(name: str) -> pd.DataFrame:
    return read(config.SILVER, name)


def read_gold(name: str) -> pd.DataFrame:
    return read(config.GOLD, name)


def exists(layer: Path, name: str) -> bool:
    return (layer / f"{name}.parquet").exists()


def espaco_livre_gb() -> float:
    """Espaço livre em GB no disco onde vive data/."""
    import shutil

    return shutil.disk_usage(config.DATA.parent).free / 1024**3


def exigir_espaco(minimo_gb: float = 3.0) -> None:
    """Aborta se disco está apertado (evita encher a máquina com PySUS)."""
    livre = espaco_livre_gb()
    if livre < minimo_gb:
        raise RuntimeError(
            f"Apenas {livre:.1f} GB livres (mínimo {minimo_gb} GB). "
            f"Limpe {config.BRONZE} ou libere espaço."
        )


def query(sql: str) -> pd.DataFrame:
    """Executa SQL podendo referenciar parquet por caminho.

    Usa os placeholders {silver} e {gold} para os diretórios das camadas.
    """
    sql = sql.format(silver=config.SILVER.as_posix(), gold=config.GOLD.as_posix())
    with connect() as con:
        return con.execute(sql).df()

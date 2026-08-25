"""Ingestão de SINAN (notificação de agravos) via PySUS.

IMPORTANTE — lição cara: `pysus.sinan(..., as_dataframe=True)` materializa o
Brasil inteiro num DataFrame pandas antes de qualquer filtro. Numa máquina
com 7,5 GB de RAM isso derrubou o processo pelo OOM killer duas vezes (RSS de
6,4 GB, confirmado em `dmesg`) — o processo simplesmente morria sem
traceback, parecendo "travado". A correção é pedir os PATHS (sem
`as_dataframe`), que já ficam em disco como Parquet, e filtrar com DuckDB
antes de tocar em pandas: o scan columnar do DuckDB nunca materializa o
Brasil inteiro em memória Python.
"""

from __future__ import annotations

import duckdb
import pandas as pd

from farol_ss import config
from farol_ss.ingest.base import Proveniencia, _agora, registrar, sha256
from farol_ss.io import duck

# Agravos disponíveis no SINAN/PySUS
AGRAVOS = {
    "DENG": "Dengue",
    "CHIK": "Chikungunya",
    "ZIKA": "Zika",
    "LEPT": "Leptospirose",
    "HEPA": "Hepatite A",
    "ESQU": "Esquistossomose",
}


def _filtrar_pe(path: str, ano: int) -> pd.DataFrame | None:
    """Filtra e agrega um Parquet do SINAN (Brasil) para PE.

    Duas lições caras embutidas aqui, ambas descobertas testando contra dado
    real, não hipotéticas:

    1. `ID_MN_RESI` no Parquet cru do DATASUS é o código de 6 dígitos SEM o
       dígito verificador (ex.: "261160" para Recife) — não um código de 7
       dígitos que baste completar com zero à esquerda. Um `lpad(...,7,'0')`
       ingênuo produz "0261160", que não bate com nenhum município e faz o
       filtro `LIKE '26%'` descartar TUDO silenciosamente. A reconstrução
       correta para 7 dígitos já existe e foi testada em
       `io.municipios.resolve_por_codigo` — reaproveitada aqui em vez de
       duplicar a lógica.

    2. O grão que interessa é *contagem de notificações* por
       `(cod_ibge, ano)`, não linhas deduplicadas. Uma versão anterior deste
       código fazia `.drop_duplicates()` sobre (código, data, classificação),
       o que colapsava em uma única linha vários casos notificados no mesmo
       dia com a mesma classificação — comum quando há um surto — subcontando
       a incidência exatamente no cenário que o IEAS existe para detectar.
    """
    from farol_ss.io import municipios as M

    con = duckdb.connect()
    cols = {
        r[0]
        for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{path}') LIMIT 0").fetchall()
    }
    col_municipio = "ID_MN_RESI" if "ID_MN_RESI" in cols else "ID_MUNICIP"
    tem_classi = "CLASSI_FIN" in cols
    tem_notific = "DT_NOTIFIC" in cols

    select_extra = ", CLASSI_FIN AS classi_fin" if tem_classi else ""
    select_data = ", DT_NOTIFIC AS dt_notific" if tem_notific else ""

    # Filtro barato por prefixo de UF (2 primeiros chars), válido tanto para
    # código de 6 quanto de 7 dígitos — a reconstrução exata do cod_ibge de 7
    # dígitos (com dígito verificador) acontece depois, em pandas, sobre o
    # subconjunto já pequeno de PE.
    sql = f"""
        SELECT CAST({col_municipio} AS VARCHAR) AS cod_bruto
            {select_extra}
            {select_data}
        FROM read_parquet('{path}')
        WHERE substr(CAST({col_municipio} AS VARCHAR), 1, 2) = '26'
    """
    df = con.execute(sql).df()
    con.close()

    if df.empty:
        return None

    df["cod_ibge"] = M.resolve_por_codigo(df["cod_bruto"])
    df = df.dropna(subset=["cod_ibge"])
    if df.empty:
        return None

    if tem_notific:
        df["ano"] = (
            pd.to_datetime(df["dt_notific"], errors="coerce").dt.year.fillna(ano).astype(int)
        )
    else:
        df["ano"] = ano

    agrupado = (
        df.groupby(["cod_ibge", "ano"], as_index=False).size().rename(columns={"size": "casos"})
    )

    if tem_classi:
        confirmados = (
            df[df["classi_fin"].astype(str).isin(["1", "10", "11", "12"])]
            .groupby(["cod_ibge", "ano"], as_index=False)
            .size()
            .rename(columns={"size": "casos_confirmados"})
        )
        agrupado = agrupado.merge(confirmados, on=["cod_ibge", "ano"], how="left")
        agrupado["casos_confirmados"] = agrupado["casos_confirmados"].fillna(0).astype(int)

    return agrupado


def ingerir_sinan() -> None:
    """Baixar e processar SINAN para cada agravo e ano, com memória contida."""
    config.preparar_pysus()  # antes de import pysus
    import pysus

    config.ensure_dirs()
    duck.exigir_espaco(minimo_gb=2.0)
    anos = config.anos()

    for agravo_cod, agravo_nome in AGRAVOS.items():
        for ano in anos:
            try:
                # Sem as_dataframe=True: devolve paths, não materializa o
                # Brasil inteiro em memória (ver docstring do módulo).
                paths = pysus.sinan(agravo_cod, ano)
                if not paths:
                    continue

                df_pe = _filtrar_pe(paths[0], ano)
                if df_pe is None or df_pe.empty:
                    print(f"  · {agravo_nome} {ano}: 0 casos em PE")
                    continue

                path = duck.write_silver(df_pe, f"sinan_{agravo_cod.lower()}_{ano}")
                registrar(
                    Proveniencia(
                        fonte=f"sinan_{agravo_cod}_{ano}",
                        url=f"pysus.sinan({agravo_cod!r}, {ano})",
                        coletado_em=_agora(),
                        arquivo=str(path.relative_to(config.ROOT)),
                        sha256=sha256(df_pe.to_csv(index=False).encode()),
                        bytes=df_pe.memory_usage(deep=True).sum().item(),
                        linhas=len(df_pe),
                        extra={"agravo": agravo_nome, "ano": ano},
                    )
                )
                total_casos = int(df_pe["casos"].sum())
                print(
                    f"  ✓ {agravo_nome} {ano}: {total_casos} casos em {df_pe.cod_ibge.nunique()} municípios"
                )

            except Exception as e:
                print(f"  ✗ {agravo_nome} {ano}: {type(e).__name__} {str(e)[:80]}")


def rodar() -> None:
    """Ingerir SINAN para todos os agravos e anos."""
    ingerir_sinan()

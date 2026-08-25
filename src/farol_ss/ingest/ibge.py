"""Ingestão de dados do IBGE: localidades, população, IPCA, malhas.

Todos os dados IBGE vêm de APIs REST documentadas. As malhas são GeoJSON.
"""

from __future__ import annotations

import geopandas as gpd
import pandas as pd

from farol_ss import config
from farol_ss.ingest.base import Fetcher, Proveniencia, _agora, registrar, sha256
from farol_ss.io import duck
from farol_ss.io import municipios as M


def _extrair_serie_populacao(data: list, ano: int) -> dict[str, int]:
    """Extrai {cod_ibge -> população} da resposta do agregado 6579.

    `localidade["id"]` já vem no formato de 7 dígitos ao consultar nível N6
    (município) — não precisa (nem deve) de nenhuma reconstrução manual do
    código. Uma versão anterior manipulava a string com `.lstrip("260")` para
    tentar "normalizar" o código; isso corrompia 22 dos 185 municípios (ex.:
    Bodocó 2602001 virava 2600001, um código de outro município), porque
    lstrip remove *caracteres*, não um prefixo — e vários municípios de PE têm
    dígitos '2', '6' ou '0' logo depois do prefixo de UF. É exatamente o tipo
    de corrupção silenciosa que a convenção de grão por cod_ibge existe para
    evitar, então a extração agora usa o id devolvido pela API tal como vem.
    """
    out: dict[str, int] = {}
    codigos_pe = M.codigos()
    for agregado in data:
        for resultado in agregado.get("resultados", []):
            for serie in resultado.get("series", []):
                cod = serie["localidade"]["id"]
                if cod not in codigos_pe:
                    continue
                valor = serie["serie"].get(str(ano))
                if valor and valor != "...":
                    out[cod] = int(float(valor))
    return out


def ingerir_populacao() -> None:
    """IBGE agregados 6579: estimativas de população por município e ano.

    2022 (ano de Censo, contagem direta em vez de estimativa) e 2023 (lacuna
    pós-censitária) vêm vazios da API — confirmado por amostragem manual, não
    é falha de rede. Anos faltantes dentro do recorte são preenchidos por
    interpolação linear entre os anos vizinhos disponíveis, e a coluna
    `fonte_dado` marca explicitamente quais linhas são IBGE direto e quais são
    interpoladas — a regra do cinza do projeto proíbe fingir que um número
    interpolado é dado primário.
    """
    anos = config.anos()
    src = config.sources()["ibge_populacao"]
    por_ano: dict[int, dict[str, int]] = {}

    with Fetcher("ibge_populacao") as f:
        for ano in anos:
            url = src["url"].format(ano=ano)
            r = f.get(url, localidades="N6[N3[26]]")
            r.raise_for_status()
            serie = _extrair_serie_populacao(r.json(), ano)
            if serie:
                por_ano[ano] = serie
                print(f"  ✓ população {ano}: {len(serie)}/185 municípios")
            else:
                print(f"  ⚠ população {ano}: API devolveu vazio (ano de Censo ou lacuna)")

    if not por_ano:
        raise RuntimeError("IBGE população: nenhum ano retornou dado")

    linhas = [
        {"cod_ibge": cod, "ano": ano, "populacao": pop, "fonte_dado": "ibge"}
        for ano, serie in por_ano.items()
        for cod, pop in serie.items()
    ]
    df = pd.DataFrame(linhas)

    faltantes = [a for a in anos if a not in por_ano]
    if faltantes:
        df = _interpolar_populacao(df, anos, faltantes)

    path = duck.write_silver(df, "ibge_populacao")
    registrar(
        Proveniencia(
            fonte="ibge_populacao",
            url=src["url"],
            coletado_em=_agora(),
            arquivo=str(path.relative_to(config.ROOT)),
            sha256=sha256(df.to_csv(index=False).encode()),
            bytes=df.memory_usage(deep=True).sum().item(),
            linhas=len(df),
            observacao=(f"anos interpolados: {faltantes}" if faltantes else None),
        )
    )


def _interpolar_populacao(df: pd.DataFrame, anos: list[int], faltantes: list[int]) -> pd.DataFrame:
    """Preenche anos sem dado por interpolação linear, por município."""
    extras = []
    for cod, grupo in df.groupby("cod_ibge"):
        serie = grupo.set_index("ano")["populacao"].reindex(anos)
        serie = serie.interpolate(method="linear", limit_direction="both")
        for ano in faltantes:
            if pd.notna(serie.get(ano)):
                extras.append(
                    {
                        "cod_ibge": cod,
                        "ano": ano,
                        "populacao": round(serie[ano]),
                        "fonte_dado": "interpolado",
                    }
                )
    if extras:
        print(f"  ↳ {len(extras)} valores interpolados para {faltantes}")
        df = pd.concat([df, pd.DataFrame(extras)], ignore_index=True)
    return df


def ingerir_ipca() -> None:
    """IBGE agregados 1737: IPCA mensal (deflator)."""
    anos = config.anos()
    periodo_min = f"{anos[0]}01"
    periodo_max = f"{anos[-1]}12"
    src = config.sources()["ibge_ipca"]

    with Fetcher("ibge_ipca") as f:
        r = f.get(src["url"].format(periodo=f"{periodo_min}-{periodo_max}"), localidades="N1[all]")
        r.raise_for_status()
        data = r.json()

        ipca_dict = {}
        for agregado in data:
            for resultado in agregado.get("resultados", []):
                for serie in resultado.get("series", []):
                    for periodo, valor in serie["serie"].items():
                        ano_mes = f"{periodo[:4]}-{periodo[4:6]}"
                        ipca_dict[ano_mes] = float(valor)

        if not ipca_dict:
            raise RuntimeError("IBGE IPCA: resposta vazia")

        df = pd.DataFrame([{"ano_mes": k, "ipca": v} for k, v in sorted(ipca_dict.items())])
        path = duck.write_silver(df, "ibge_ipca")
        registrar(
            Proveniencia(
                fonte="ibge_ipca",
                url=str(r.url),
                coletado_em=_agora(),
                arquivo=str(path.relative_to(config.ROOT)),
                sha256=sha256(df.to_csv(index=False).encode()),
                bytes=df.memory_usage(deep=True).sum().item(),
                linhas=len(df),
            )
        )


def ingerir_malhas() -> None:
    """IBGE v3: GeoJSON das malhas municipais de PE (simplificado)."""
    src = config.sources()["ibge_malhas"]
    url = src["url"]
    params = src.get("params", {})

    with Fetcher("ibge_malhas") as f:
        r = f.get(url, **params)
        r.raise_for_status()

        geo = r.json()
        gdf = gpd.GeoDataFrame.from_features(geo["features"])
        gdf.rename(columns={"codarea": "cod_ibge"}, inplace=True)
        gdf["cod_ibge"] = gdf["cod_ibge"].astype(str).str.zfill(7)

        codigos_pe = M.codigos()
        antes = len(gdf)
        gdf = gdf[gdf["cod_ibge"].isin(codigos_pe)]
        if len(gdf) != antes:
            print(f"  ⚠ malhas: {antes - len(gdf)} feições fora do recorte de PE descartadas")
        if len(gdf) != len(codigos_pe):
            print(f"  ⚠ malhas: {len(gdf)}/{len(codigos_pe)} municípios com geometria")

        # Simplificar geometria (0.001 ≈ 100m em lat/lon) antes de servir ao Folium
        gdf["geometry"] = gdf.geometry.simplify(0.001, preserve_topology=True)

        path = config.BRONZE / "ibge_malhas.parquet"
        gdf.to_parquet(path)

        registrar(
            Proveniencia(
                fonte="ibge_malhas",
                url=str(r.url),
                coletado_em=_agora(),
                arquivo=str(path.relative_to(config.ROOT)),
                sha256=sha256(r.content),
                bytes=len(r.content),
                linhas=len(gdf),
            )
        )


def rodar() -> None:
    """Ingerir todos os dados IBGE."""
    config.ensure_dirs()
    duck.exigir_espaco()
    ingerir_populacao()
    ingerir_ipca()
    ingerir_malhas()

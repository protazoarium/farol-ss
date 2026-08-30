"""Ingestão do CadÚnico — subíndice de vulnerabilidade socioeconômica.

Fonte: a **Matriz de Informações Sociais (MI Social)** do SAGI/MDS, exposta
como um índice Solr em `aplicacoes.mds.gov.br/sagi/servicos/misocial`. Não é
documentada como "API", mas responde a consultas Solr padrão (`q`, `fq`,
`fl`, `rows`) e cobre os 5.570 municípios mês a mês.

Campos usados (por município, na competência de dezembro de cada ano):
- `cadun_qtde_fam_sit_extrema_pobreza_s` — famílias em extrema pobreza no CadÚnico
- `cadun_qtd_familias_cadastradas_i` — total de famílias cadastradas
- `populacao_estimada_ibge_ano_i` — população

O subíndice é a **taxa de famílias em extrema pobreza por mil habitantes** —
uma medida de intensidade da pobreza territorial, comparável entre municípios
via rank percentil no `index/ieas.py`. A taxa é calculada na camada gold
(`transform/gold_municipio_ano.py`) usando a população oficial do IBGE já
ingerida; o silver guarda só as contagens brutas.
"""

from __future__ import annotations

import pandas as pd

from farol_ss import config
from farol_ss.ingest.base import Fetcher, Proveniencia, _agora, registrar, sha256
from farol_ss.io import duck
from farol_ss.io import municipios as M

_URL = "https://aplicacoes.mds.gov.br/sagi/servicos/misocial"
_FL = (
    "codigo_ibge,cadun_qtde_fam_sit_extrema_pobreza_s,"
    "cadun_qtd_familias_cadastradas_i,populacao_estimada_ibge_ano_i"
)


def _int(v) -> float | None:
    try:
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return None


def _consultar_ano(f: Fetcher, ano: int) -> pd.DataFrame:
    """Competência de dezembro do ano — o retrato mais completo da série anual."""
    r = f.get(
        _URL,
        q="*:*",
        fq=["sigla_uf:PE", f"anomes:{ano}12"],
        fl=_FL,
        rows=300,
        wt="json",
    )
    r.raise_for_status()
    docs = r.json().get("response", {}).get("docs", [])
    linhas = []
    for d in docs:
        cod_ibge = M.resolve_por_codigo(pd.Series([d.get("codigo_ibge")])).iloc[0]
        if pd.isna(cod_ibge):
            continue
        fam_ext = _int(d.get("cadun_qtde_fam_sit_extrema_pobreza_s"))
        pop = _int(d.get("populacao_estimada_ibge_ano_i"))
        linhas.append(
            {
                "cod_ibge": cod_ibge,
                "ano": ano,
                "familias_extrema_pobreza": fam_ext,
                "familias_cadastradas": _int(d.get("cadun_qtd_familias_cadastradas_i")),
                "populacao_sagi": pop,
            }
        )
    return pd.DataFrame(
        linhas,
        columns=[
            "cod_ibge",
            "ano",
            "familias_extrema_pobreza",
            "familias_cadastradas",
            "populacao_sagi",
        ],
    )


def ingerir_cadunico() -> pd.DataFrame:
    config.ensure_dirs()
    partes = []
    with Fetcher("cadunico") as f:
        for ano in config.anos():
            try:
                df = _consultar_ano(f, ano)
            except Exception as e:  # noqa: BLE001 — ano ausente não derruba a série
                print(f"    ⚠ CadÚnico {ano}: {type(e).__name__} {str(e)[:60]}")
                continue
            if not df.empty:
                partes.append(df)
                print(f"    ✓ CadÚnico {ano}: {len(df)} municípios")

    if not partes:
        raise RuntimeError("CadÚnico/SAGI: nenhuma competência retornou dado.")

    out = pd.concat(partes, ignore_index=True)
    path = duck.write_silver(out, "cadunico")
    registrar(
        Proveniencia(
            fonte="cadunico",
            url=_URL,
            coletado_em=_agora(),
            arquivo=str(path.relative_to(config.ROOT)),
            sha256=sha256(out.to_csv(index=False).encode()),
            bytes=out.memory_usage(deep=True).sum().item(),
            linhas=len(out),
            observacao="MI Social (SAGI/MDS), índice Solr; competência dez/ano; taxa de famílias em extrema pobreza",
            extra={
                "municipios": out["cod_ibge"].nunique(),
                "anos": sorted(out["ano"].unique().tolist()),
            },
        )
    )
    print(f"  ✓ cadunico: {len(out)} linhas, {out['cod_ibge'].nunique()} municípios")
    return out


def rodar() -> None:
    ingerir_cadunico()

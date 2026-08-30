"""Ingestão do saneamento — Censo 2022 do IBGE (substituto do SNIS).

O SNIS foi encerrado em 2023 e o domínio da série histórica não resolve. O
Censo 2022 traz, por município (nível N6), a distribuição dos domicílios
particulares permanentes ocupados por:

- forma de abastecimento de água  — agregado **6803**
- tipo de esgotamento sanitário    — agregado **6805**
- destino do lixo                  — agregado **6892**

Deste conjunto extraímos três coberturas e, delas, o **déficit** (1 − cobertura):

| Cobertura | Numerador (categoria adequada) | Denominador |
|---|---|---|
| água | "Possui ligação à rede geral e a utiliza como forma principal" (72144) | Total (72129) |
| esgoto | "Rede geral, rede pluvial ou fossa ligada à rede" (46290) | Total (46292) |
| lixo | "Coletado" (2520) | Total (10972) |

O subíndice de saneamento (peso e composição em `conf/ieas.yml`) é
`0,35·déficit_água + 0,45·déficit_esgoto + 0,20·déficit_lixo`. É um retrato de
2022 aplicado a todo o recorte — o saneamento muda devagar e é a única fonte
censitária disponível; documentado como limitação.
"""

from __future__ import annotations

import pandas as pd

from farol_ss import config
from farol_ss.ingest.base import Fetcher, Proveniencia, _agora, registrar, sha256
from farol_ss.io import municipios as M

_API = "https://servicodados.ibge.gov.br/api/v3/agregados"

# agregado → (classificação, categoria "adequada", categoria "total"), nome curto
_INDICADORES = {
    "cob_agua": (6803, 1821, 72144, 72129),
    "cob_esgoto": (6805, 11558, 46290, 46292),
    "cob_lixo": (6892, 67, 2520, 10972),
}


def _cobertura(
    f: Fetcher, agregado: int, classif: int, cat_ok: int, cat_total: int
) -> dict[str, float]:
    """Fração de domicílios na categoria adequada, por município de PE.

    A API devolve um `resultado` por categoria pedida; cada um tem uma única
    chave em `classificacoes[0]["categoria"]` (o id da categoria) e as séries
    por município. Aqui remontamos {município: {categoria: valor}} e dividimos.
    """
    r = f.get(
        f"{_API}/{agregado}/periodos/2022/variaveis/381",
        localidades="N6[N3[26]]",
        classificacao=f"{classif}[{cat_ok},{cat_total}]",
    )
    r.raise_for_status()

    por_municipio: dict[str, dict[int, float]] = {}
    for var in r.json():
        for res in var.get("resultados", []):
            cat_id = int(next(iter(res["classificacoes"][0]["categoria"])))
            for serie in res["series"]:
                cod = serie["localidade"]["id"]
                if cod not in M.codigos():
                    continue
                val = serie["serie"].get("2022")
                if val in (None, "...", "-", ".."):
                    continue
                por_municipio.setdefault(cod, {})[cat_id] = float(val)

    return {
        cod: vals[cat_ok] / vals[cat_total]
        for cod, vals in por_municipio.items()
        if vals.get(cat_total) and cat_ok in vals
    }


def ingerir_saneamento() -> pd.DataFrame:
    config.ensure_dirs()
    colunas: dict[str, dict[str, float]] = {}
    with Fetcher("ibge_saneamento") as f:
        for nome, (agregado, classif, cat_ok, cat_total) in _INDICADORES.items():
            colunas[nome] = _cobertura(f, agregado, classif, cat_ok, cat_total)
            print(f"    ✓ {nome}: {len(colunas[nome])} municípios")

    df = pd.DataFrame(colunas).reset_index(names="cod_ibge")
    df["deficit_agua"] = 1 - df["cob_agua"]
    df["deficit_esgoto"] = 1 - df["cob_esgoto"]
    df["deficit_lixo"] = 1 - df["cob_lixo"]

    conf = config.ieas_conf()["necessidade"]["saneamento"]["pesos"]
    df["sub_saneamento_bruto"] = (
        conf["deficit_agua"] * df["deficit_agua"]
        + conf["deficit_esgoto"] * df["deficit_esgoto"]
        + conf["deficit_residuos"] * df["deficit_lixo"]
    )

    path = config.SILVER / "ibge_saneamento.parquet"
    df.to_parquet(path, index=False)
    registrar(
        Proveniencia(
            fonte="ibge_saneamento",
            url=f"{_API}/{{6803|6805|6892}}/periodos/2022/variaveis/381",
            coletado_em=_agora(),
            arquivo=str(path.relative_to(config.ROOT)),
            sha256=sha256(df.to_csv(index=False).encode()),
            bytes=df.memory_usage(deep=True).sum().item(),
            linhas=len(df),
            observacao="Censo 2022 — déficit de água/esgoto/lixo; retrato único aplicado a todo o recorte (SNIS encerrado).",
            extra={"municipios": df["cod_ibge"].nunique()},
        )
    )
    print(f"  ✓ ibge_saneamento: {len(df)} municípios")
    return df


def rodar() -> None:
    ingerir_saneamento()

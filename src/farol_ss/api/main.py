"""API aberta do Farol-SS — JSON/CSV sobre a camada gold, sem autenticação.

Serve o que o pipeline já materializou em `data/gold/`. Não recalcula nada:
se o número está errado aqui, está errado no Parquet, e o conserto é no
pipeline, não na API. `?formato=csv` em qualquer rota devolve text/csv.

    uv run uvicorn farol_ss.api.main:api --port 8000     # ou: make api
    http://localhost:8000/docs                            # Swagger
"""

from __future__ import annotations

import io
import json

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse

from farol_ss import config
from farol_ss.io import duck
from farol_ss.io import municipios as M

api = FastAPI(
    title="Farol da Saúde & Saneamento — API aberta",
    description="Índice de Efetividade da Alocação Sanitária (IEAS) para os 185 municípios de PE.",
    version="1.0.0",
)


def _entrega(df: pd.DataFrame, formato: str):
    """JSON (lista de registros) ou CSV, conforme `?formato=`."""
    if formato == "csv":
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        return StreamingResponse(
            iter([buf.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=farol_ss.csv"},
        )
    # via to_json: NaN vira `null` (JSON válido), datas viram ISO. json.dumps
    # direto sobre to_dict() quebra em NaN ("Out of range float values").
    return JSONResponse(json.loads(df.to_json(orient="records", date_format="iso")))


def _gold(nome: str) -> pd.DataFrame:
    try:
        return duck.read_gold(nome)
    except FileNotFoundError as e:  # pipeline não rodou
        raise HTTPException(503, f"Camada gold ausente: {e}") from e


@api.get("/", include_in_schema=False)
def raiz():
    return {
        "projeto": "Farol da Saúde & Saneamento",
        "rotas": ["/municipios", "/municipios/{cod_ibge}", "/ieas", "/alertas", "/fontes"],
        "docs": "/docs",
    }


@api.get("/municipios", tags=["dimensão"])
def municipios(formato: str = Query("json", pattern="^(json|csv)$")):
    """Os 185 municípios de PE com meso/microrregião."""
    cols = ["cod_ibge", "nome", "mesorregiao", "microrregiao", "regiao_intermediaria"]
    return _entrega(M.municipios()[cols], formato)


@api.get("/municipios/{cod_ibge}", tags=["dimensão"])
def municipio(cod_ibge: str, formato: str = Query("json", pattern="^(json|csv)$")):
    """Série completa (todos os anos) de um município: população, casos, taxas,
    L3, subíndices, gap e farol."""
    if cod_ibge not in M.codigos():
        raise HTTPException(404, f"{cod_ibge} não é um município de PE.")
    df = _gold("ieas")
    return _entrega(df[df["cod_ibge"] == cod_ibge].sort_values("ano"), formato)


@api.get("/ieas", tags=["índice"])
def ieas(
    ano: int | None = Query(None, ge=2020, le=2024),
    farol: str | None = Query(None, pattern="^(vermelho|amarelo|verde|azul|cinza)$"),
    formato: str = Query("json", pattern="^(json|csv)$"),
):
    """IEAS por município-ano. Filtra por `ano` e/ou cor do `farol`."""
    df = _gold("ieas")
    if ano is not None:
        df = df[df["ano"] == ano]
    if farol is not None:
        df = df[df["farol"] == farol]
    cols = [
        "cod_ibge",
        "ano",
        "populacao",
        "necessidade_rank",
        "alocacao_rank",
        "necessidade_cobertura",
        "alocacao_cobertura",
        "gap",
        "ieas",
        "farol",
        # transparência sobre as limitações de dado (ver docs/relatorio-tecnico.md §10)
        "l3_maturidade_pncp_uf",  # fração de municípios de PE no PNCP naquele ano
        "saneamento_ano_referencia",  # o subíndice de saneamento é um retrato de 2022
    ]
    return _entrega(df[[c for c in cols if c in df.columns]], formato)


@api.get("/alertas", tags=["índice"])
def alertas(
    tipo: str | None = None,
    ano: int | None = Query(None, ge=2020, le=2024),
    formato: str = Query("json", pattern="^(json|csv)$"),
):
    """Alertas explicáveis (desalinhamento estrutural, suspeita de desabastecimento)."""
    if not duck.exists(config.GOLD, "alertas"):
        return _entrega(
            pd.DataFrame(columns=["cod_ibge", "ano", "tipo", "severidade", "explicacao"]), formato
        )
    df = duck.read_gold("alertas")
    if tipo is not None:
        df = df[df["tipo"] == tipo]
    if ano is not None:
        df = df[df["ano"] == ano]
    return _entrega(df, formato)


@api.get("/fontes", tags=["proveniência"])
def fontes(formato: str = Query("json", pattern="^(json|csv)$")):
    """Catálogo de fontes com link para o conjunto no dados.gov.br, licença e
    resumo da última coleta (manifest.json)."""
    from farol_ss import proveniencia

    return _entrega(proveniencia.tabela(), formato)

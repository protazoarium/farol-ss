"""Ingestão de itens de contratação do PNCP — nível de item, com preço unitário.

O endpoint de consulta usado em `ingest/pncp.py`
(`/v1/contratacoes/publicacao`) só devolve o valor TOTAL da compra. O preço
unitário por item vive em outro recurso:

    GET https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{sequencial}/itens

que devolve `descricao`, `valorUnitarioEstimado`, `quantidade`,
`unidadeMedida`, `materialOuServico` e a categoria do item. É isso que
viabiliza o detector 3 (sobrepreço) em `index/anomalies.py`.

Como são ~6 mil contratações e o PNCP é instável, a ingestão:
- só busca as contratações cujo `objeto_compra` casa com palavra-chave de
  saúde/insumo (as demais não interessam ao detector de sobrepreço);
- é RETOMÁVEL: pula o que já está em `silver/pncp_itens.parquet`;
- aceita um teto (`limite`) por execução.
"""

from __future__ import annotations

import re
import unicodedata

import pandas as pd

from farol_ss import config
from farol_ss.ingest.base import Fetcher, Proveniencia, _agora, registrar, sha256
from farol_ss.io import duck


def _sem_acento(texto: str) -> str:
    s = unicodedata.normalize("NFKD", str(texto).lower())
    return "".join(c for c in s if not unicodedata.combining(c))


# Fragmentos (sem acento) que marcam uma contratação como "de saúde/insumo" —
# o universo em que faz sentido procurar sobrepreço de item. Deliberadamente
# amplo: um falso-positivo aqui só custa uma chamada de API a mais, não um
# alerta (o alerta ainda depende do casamento estrito por categoria).
_KEYWORDS = [
    "medicament", "farmac", "insumo", "hospitalar", "saude", "vacina", "seringa",
    "larvicida", "inseticida", "reagente", "laboratori", "odontolog", "curativo",
    "antibiotic", "analgesic", "dipirona", "paracetamol", "material medic",
    "equipamento medic", "teste rapido",
]  # fmt: skip

_COLUNAS = [
    "cod_ibge",
    "ano",
    "numero_controle_pncp",
    "numero_item",
    "descricao",
    "material_ou_servico",
    "quantidade",
    "unidade_medida",
    "valor_unitario_estimado",
    "valor_total",
    "item_categoria_nome",
    "orcamento_sigiloso",
]


def _decompoe_controle(numero_controle: str) -> tuple[str, int, int] | None:
    """`11049848000121-1-000001/2023` → (cnpj, ano, sequencial)."""
    m = re.match(r"^(\d{14})-\d+-(\d+)/(\d{4})$", str(numero_controle).strip())
    if not m:
        return None
    cnpj, seq, ano = m.group(1), int(m.group(2)), int(m.group(3))
    return cnpj, ano, seq


# Modalidades onde se compram INSUMOS (com preço unitário comparável): Pregão
# eletrônico/presencial, Dispensa, Inexigibilidade. Concorrência é obra —
# item de valor global, sem preço unitário que faça sentido comparar.
_MODALIDADES_INSUMO = {6, 7, 8, 9}


def _candidatas(compras: pd.DataFrame) -> pd.DataFrame:
    obj = compras["objeto_compra"].fillna("").map(_sem_acento)
    mask = obj.apply(lambda t: any(k in t for k in _KEYWORDS))
    mask &= compras["modalidade_id"].isin(_MODALIDADES_INSUMO)
    return compras.loc[mask, ["cod_ibge", "ano", "numero_controle_pncp", "objeto_compra"]]


def ingerir_itens(limite: int | None = None) -> pd.DataFrame:
    """Busca os itens das contratações de saúde ainda não coletadas.

    `limite` limita quantas contratações NOVAS buscar nesta execução (útil
    para não segurar o terminal 6 min de uma vez). Sem `limite`, vai até o
    fim. Devolve o `pncp_itens.parquet` consolidado (o que já havia + novo).
    """
    if not duck.exists(config.SILVER, "pncp"):
        raise FileNotFoundError("silver/pncp.parquet não existe — rode `farol silver` antes.")

    compras = duck.read_silver("pncp")
    alvo = _candidatas(compras).drop_duplicates("numero_controle_pncp")

    ja_feito: set[str] = set()
    existente: pd.DataFrame | None = None
    if duck.exists(config.SILVER, "pncp_itens"):
        existente = duck.read_silver("pncp_itens")
        ja_feito = set(existente["numero_controle_pncp"])

    pendentes = alvo[~alvo["numero_controle_pncp"].isin(ja_feito)]
    if limite is not None:
        pendentes = pendentes.head(limite)

    print(
        f"  itens PNCP: {len(alvo)} contratações de saúde, "
        f"{len(ja_feito)} já coletadas, {len(pendentes)} nesta execução"
    )

    novas_linhas: list[dict] = []
    with Fetcher("pncp_itens") as f:
        for row in pendentes.itertuples():
            partes = _decompoe_controle(row.numero_controle_pncp)
            if partes is None:
                continue
            cnpj, ano, seq = partes
            url = f"https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{seq}/itens"
            try:
                r = f.get(url)
                if r.status_code in (404, 204) or not r.content:
                    continue
                r.raise_for_status()
                itens = r.json()
            except Exception as e:  # noqa: BLE001 — fonte instável não derruba a ingestão
                print(f"    ⚠ {row.numero_controle_pncp}: {type(e).__name__}")
                continue

            for it in itens:
                novas_linhas.append(
                    {
                        "cod_ibge": row.cod_ibge,
                        "ano": row.ano,
                        "numero_controle_pncp": row.numero_controle_pncp,
                        "numero_item": it.get("numeroItem"),
                        "descricao": it.get("descricao"),
                        "material_ou_servico": it.get("materialOuServicoNome"),
                        "quantidade": it.get("quantidade"),
                        "unidade_medida": it.get("unidadeMedida"),
                        "valor_unitario_estimado": it.get("valorUnitarioEstimado"),
                        "valor_total": it.get("valorTotal"),
                        "item_categoria_nome": it.get("itemCategoriaNome"),
                        "orcamento_sigiloso": it.get("orcamentoSigiloso"),
                    }
                )

    novo = pd.DataFrame(novas_linhas, columns=_COLUNAS)
    consolidado = novo if existente is None else pd.concat([existente, novo], ignore_index=True)
    path = duck.write_silver(consolidado, "pncp_itens")
    registrar(
        Proveniencia(
            fonte="pncp_itens",
            url="https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{seq}/itens",
            coletado_em=_agora(),
            arquivo=str(path.relative_to(config.ROOT)),
            sha256=sha256(consolidado.to_csv(index=False).encode()),
            bytes=consolidado.memory_usage(deep=True).sum().item(),
            linhas=len(consolidado),
            extra={"contratacoes_coletadas": consolidado["numero_controle_pncp"].nunique()},
        )
    )
    print(
        f"  ✓ pncp_itens: {len(consolidado)} itens de {consolidado['numero_controle_pncp'].nunique()} contratações"
    )
    return consolidado


def rodar(limite: int | None = None) -> None:
    ingerir_itens(limite=limite)

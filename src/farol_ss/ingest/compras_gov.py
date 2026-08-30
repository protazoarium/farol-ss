"""Ingestão do Compras.gov.br (dados abertos) — camada L3 **federal**.

Complemento de escopo federal ao L3 municipal do PNCP (`ingest/pncp.py`). O
PNCP registra o que as **prefeituras** contratam; este módulo pega o que
**órgãos federais sediados em municípios de PE** contratam em saúde/insumos,
geolocalizado por `unidadeOrgaoCodigoIbge`.

Endpoint: `/modulo-contratacoes/1_consultarContratacoes_PNCP_14133` do
`dadosabertos.compras.gov.br` (API aberta, sem chave). É o espelho das
contratações sob a Lei 14.133/2021; por isso filtramos **apenas a esfera
federal** (`orgaoEntidadeEsferaId == "F"`) — as contratações municipais aqui
seriam as mesmas já coletadas do PNCP, e somá-las duplicaria o L3.

Cobertura: 2021–2024 (a Lei 14.133 e este cadastro começam em 2021; o L3 de
2020 já é reconhecidamente ralo — ver `docs/relatorio-tecnico.md` §10).

O valor federal é somado ao L3 municipal no gold (`transform/gold_municipio_ano.py`),
mantendo um único eixo/coluna `l3_per_capita` e os pesos do IEAS intactos.
"""

from __future__ import annotations

import time
import unicodedata

import pandas as pd

from farol_ss import config
from farol_ss.ingest.base import Fetcher, Proveniencia, _agora, registrar, sha256
from farol_ss.io import duck
from farol_ss.io import municipios as M

_BASE = "https://dadosabertos.compras.gov.br/modulo-contratacoes/1_consultarContratacoes_PNCP_14133"
# codigoModalidade do Compras.gov.br (≠ códigos do PNCP): onde se compram
# insumos de saúde com valor comparável. 3=Concorrência-E, 5=Pregão-E,
# 6=Dispensa, 7=Inexigibilidade.
_MODALIDADES = {3: "Concorrência", 5: "Pregão eletrônico", 6: "Dispensa", 7: "Inexigibilidade"}
_ANOS = (2021, 2022, 2023, 2024)
_TAMANHO_PAGINA = 500
_PAUSA_S = 0.25


def _sem_acento(texto: str) -> str:
    s = unicodedata.normalize("NFKD", str(texto).lower())
    return "".join(c for c in s if not unicodedata.combining(c))


# fragmentos que marcam a contratação como de saúde/insumo (mesma lógica ampla
# de ingest/pncp_itens.py — um falso-positivo aqui só infla o L3 federal de um
# município com órgão federal de saúde, e é filtrado pela esfera)
_KEYWORDS = [
    "medicament", "farmac", "insumo hospitalar", "insumo de saude", "hospitalar",
    "material medico", "material hospitalar", "vacina", "seringa", "laboratori",
    "reagente", "odontolog", "curativo", "antibiotic", "equipamento medic",
    "equipamento hospitalar", "teste rapido", "correlato", "saude publica",
    "enfermagem", "cirurgic",
]  # fmt: skip

_COLUNAS = [
    "cod_ibge",
    "ano",
    "numero_controle_pncp",
    "modalidade_nome",
    "objeto_compra",
    "valor_total_homologado",
    "valor_total_estimado",
    "orgao_razao_social",
]


def _e_saude(objeto: str) -> bool:
    t = _sem_acento(objeto)
    return any(k in t for k in _KEYWORDS)


def _linha_federal_de_saude(c: dict, ano: int, cm_nome: str, codigos_pe: set[str]) -> dict | None:
    """Aceita a contratação só se for **esfera federal**, em município de PE e
    de saúde. Esfera municipal aqui é a mesma do PNCP — descartar para não
    duplicar o L3."""
    if c.get("orgaoEntidadeEsferaId") != "F":
        return None
    cod = str(c.get("unidadeOrgaoCodigoIbge") or "")
    if cod not in codigos_pe:
        return None
    objeto = c.get("objetoCompra") or ""
    if not _e_saude(objeto):
        return None
    return {
        "cod_ibge": cod,
        "ano": ano,
        "numero_controle_pncp": c.get("numeroControlePNCP"),
        "modalidade_nome": cm_nome,
        "objeto_compra": objeto,
        "valor_total_homologado": c.get("valorTotalHomologado"),
        "valor_total_estimado": c.get("valorTotalEstimado"),
        "orgao_razao_social": c.get("orgaoEntidadeRazaoSocial"),
    }


def _contratacoes_ano_modalidade(f: Fetcher, ano: int, cm: int) -> list[dict]:
    """Todas as contratações de um (ano, modalidade) para PE — janela anual,
    página de 500. São poucas páginas (≤ ~3 por modalidade-ano)."""
    registros: list[dict] = []
    pagina = 1
    while pagina <= 50:
        r = f.get(
            _BASE,
            pagina=pagina,
            tamanhoPagina=_TAMANHO_PAGINA,
            dataPublicacaoPncpInicial=f"{ano}-01-01",
            dataPublicacaoPncpFinal=f"{ano}-12-31",
            codigoModalidade=cm,
            unidadeOrgaoUfSigla="PE",
        )
        r.raise_for_status()
        corpo = r.json() if r.content else {}
        lote = corpo.get("resultado", [])
        registros.extend(lote)
        total_pag = int(corpo.get("totalPaginas", 0) or 0)
        if pagina >= total_pag or not lote:
            break
        pagina += 1
        time.sleep(_PAUSA_S)
    return registros


def ingerir_compras_gov() -> pd.DataFrame:
    config.ensure_dirs()
    codigos_pe = M.codigos()
    linhas: list[dict] = []

    with Fetcher("compras_gov") as f:
        for ano in _ANOS:
            achados_ano = 0
            for cm, cm_nome in _MODALIDADES.items():
                try:
                    registros = _contratacoes_ano_modalidade(f, ano, cm)
                except Exception as e:  # noqa: BLE001 — API instável não derruba
                    print(f"    ⚠ {ano} mod {cm}: {type(e).__name__} {str(e)[:60]}")
                    continue
                for c in registros:
                    linha = _linha_federal_de_saude(c, ano, cm_nome, codigos_pe)
                    if linha is not None:
                        linhas.append(linha)
                        achados_ano += 1
                time.sleep(_PAUSA_S)
            print(f"  · compras.gov.br {ano}: {achados_ano} contratações federais de saúde em PE")

    df = pd.DataFrame(linhas, columns=_COLUNAS).drop_duplicates("numero_controle_pncp")
    path = duck.write_silver(df, "compras_gov")
    n_mun = df["cod_ibge"].nunique() if not df.empty else 0
    registrar(
        Proveniencia(
            fonte="compras_gov",
            url=_BASE + "?unidadeOrgaoUfSigla=PE&codigoModalidade={3,5,6,7}",
            coletado_em=_agora(),
            arquivo=str(path.relative_to(config.ROOT)),
            sha256=sha256(df.to_csv(index=False).encode()),
            bytes=df.memory_usage(deep=True).sum().item(),
            linhas=len(df),
            observacao=(
                "L3 FEDERAL: contratações de saúde de órgãos da esfera federal "
                "sediados em municípios de PE (unidadeOrgaoCodigoIbge). Complementa "
                "o L3 municipal do PNCP; esfera municipal excluída para não duplicar."
            ),
            extra={
                "municipios": n_mun,
                "anos": sorted(df["ano"].unique().tolist()) if not df.empty else [],
            },
        )
    )
    print(f"  ✓ compras_gov: {len(df)} contratações federais de saúde, {n_mun} municípios")
    return df


def rodar() -> None:
    ingerir_compras_gov()

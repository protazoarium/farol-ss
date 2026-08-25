"""Sondagem das fontes federais: o que está realmente disponível para PE?

Roda ANTES de qualquer código de índice. Fontes governamentais têm buracos —
descobrir que o SNIS cobre só parte dos municípios precisa acontecer no dia 1,
não na véspera da entrega. Cada sonda baixa uma amostra pequena e reporta
alcançabilidade, formato e cobertura municipal, sem construir nada.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from farol_ss import config
from farol_ss.ingest.base import Fetcher


@dataclass
class Resultado:
    fonte: str
    ok: bool
    detalhe: str
    cobertura: str = "—"


def _codigos_pe() -> set[str]:
    from farol_ss.io.municipios import codigos

    return codigos()


def _erro(e: Exception) -> str:
    if isinstance(e, httpx.HTTPStatusError):
        return f"HTTP {e.response.status_code}"
    return f"{type(e).__name__}: {str(e)[:80]}"


def sonda_ibge_localidades() -> Resultado:
    with Fetcher("ibge_municipios") as f:
        try:
            d = f.get(config.sources()["ibge_municipios"]["url"]).json()
            return Resultado("IBGE localidades", True, f"{len(d)} municípios", f"{len(d)}/185")
        except Exception as e:
            return Resultado("IBGE localidades", False, _erro(e))


def sonda_ibge_populacao() -> Resultado:
    ano = config.recorte()["ano_fim"]
    url = config.sources()["ibge_populacao"]["url"].format(ano=ano)
    with Fetcher("ibge_populacao") as f:
        try:
            d = f.get(url, localidades="N6[N3[26]]").json()
            series = d[0]["resultados"][0]["series"]
            return Resultado("IBGE população", True, f"estimativas {ano}", f"{len(series)}/185")
        except Exception as e:
            return Resultado("IBGE população", False, _erro(e))


def sonda_ibge_ipca() -> Resultado:
    r = config.recorte()
    periodo = f"{r['ano_inicio']}01-{r['ano_fim']}12"
    url = config.sources()["ibge_ipca"]["url"].format(periodo=periodo)
    with Fetcher("ibge_ipca") as f:
        try:
            d = f.get(url, localidades="N1[all]").json()
            n = len(d[0]["resultados"][0]["series"][0]["serie"])
            return Resultado("IBGE IPCA", True, f"{n} meses de índice")
        except Exception as e:
            return Resultado("IBGE IPCA", False, _erro(e))


def sonda_ibge_malhas() -> Resultado:
    with Fetcher("ibge_malhas") as f:
        try:
            r = f.get(
                config.sources()["ibge_malhas"]["url"],
                formato="application/vnd.geo+json",
                qualidade="intermediaria",
                intrarregiao="municipio",
            )
            r.raise_for_status()
            feats = r.json().get("features", [])
            kb = len(r.content) // 1024
            return Resultado("IBGE malhas", True, f"GeoJSON {kb} KB", f"{len(feats)}/185")
        except Exception as e:
            return Resultado("IBGE malhas", False, _erro(e))


def sonda_transparencia() -> Resultado:
    chave = config.transparencia_key()
    if not chave:
        return Resultado(
            "Transparência (CGU)",
            False,
            "sem PORTAL_TRANSPARENCIA_API_KEY — chave gratuita via login gov.br",
        )
    url = config.sources()["transparencia"]["url"]
    with Fetcher("transparencia", headers={"chave-api-dados": chave}) as f:
        try:
            r = f.get(
                url, mesAnoInicio="01/2024", mesAnoFim="12/2024", codigoIbge="2611606", pagina=1
            )
            r.raise_for_status()
            return Resultado(
                "Transparência (CGU)", True, f"{len(r.json())} registros p/ Recife 2024"
            )
        except Exception as e:
            return Resultado("Transparência (CGU)", False, _erro(e))


def sonda_pncp() -> Resultado:
    url = "https://pncp.gov.br/api/consulta/v1/contratos"
    with Fetcher("pncp") as f:
        try:
            r = f.get(url, dataInicial="20240101", dataFinal="20240131", pagina=1, tamanhoPagina=10)
            r.raise_for_status()
            body = r.json()
            total = body.get("totalRegistros", "?")
            return Resultado("PNCP", True, f"{total} contratos em jan/2024 (Brasil)")
        except Exception as e:
            return Resultado("PNCP", False, _erro(e))


def sonda_compras_gov() -> Resultado:
    url = "https://dadosabertos.compras.gov.br/modulo-uasg/1_consultarUasg"
    with Fetcher("compras_gov") as f:
        try:
            # statusUasg é obrigatório; sem ele a API devolve 404
            r = f.get(url, pagina=1, siglaUf="PE", statusUasg=True)
            r.raise_for_status()
            body = r.json()
            total = body.get("totalRegistros", 0)
            uasgs = body.get("resultado", [])
            # codigoMunicipioIbge é o que permite geolocalizar a compra federal
            muns = {str(u.get("codigoMunicipioIbge")) for u in uasgs} & _codigos_pe()
            return Resultado(
                "Compras.gov.br",
                True,
                f"{total} UASGs em PE",
                f"{len(muns)}/185 (1ª pág.)",
            )
        except Exception as e:
            return Resultado("Compras.gov.br", False, _erro(e))


def sonda_snis() -> Resultado:
    url = "https://dadosabertos.cidades.gov.br/api/3/action/package_search"
    with Fetcher("snis") as f:
        try:
            r = f.get(url, q="snis serie historica", rows=5)
            r.raise_for_status()
            n = r.json()["result"]["count"]
            return Resultado("SNIS (CKAN)", True, f"{n} conjuntos encontrados")
        except Exception as e:
            return Resultado("SNIS (CKAN)", False, _erro(e))


def sonda_dados_gov() -> Resultado:
    """O catálogo do dados.gov.br passou a exigir chave na API.

    Não é dependência de dado — as fontes são baixadas dos portais de origem.
    Serve apenas para citar os conjuntos na página de Metodologia, e os links
    do catálogo estão fixos em conf/sources.yml. Falha aqui não bloqueia nada.
    """
    with Fetcher("dados_gov") as f:
        try:
            r = f.get("https://dados.gov.br/api/publico/conjuntos-dados", nomeConjuntoDados="SIOPS")
            if r.status_code == 401:
                return Resultado(
                    "dados.gov.br",
                    True,
                    "API exige chave; links do catálogo fixos em sources.yml",
                )
            r.raise_for_status()
            return Resultado("dados.gov.br", True, "catálogo acessível")
        except Exception as e:
            return Resultado("dados.gov.br", False, _erro(e))


def sonda_sinan() -> Resultado:
    """SINAN é a espinha dorsal do eixo epidemiológico.

    Baixa o Brasil inteiro (não há filtro por UF na API), então a ingestão
    precisa recortar PE e descartar o bruto logo em seguida.
    """
    config.preparar_pysus()
    try:
        import pysus
    except ImportError:
        return Resultado("SINAN (PySUS)", False, "não instalado — uv sync --extra sus")
    try:
        ano = config.recorte()["ano_fim"] - 1
        df = pysus.sinan("DENG", ano, as_dataframe=True)
        # Incidência é por município de RESIDÊNCIA (ID_MN_RESI), não de notificação.
        col = "ID_MN_RESI" if "ID_MN_RESI" in df.columns else "ID_MUNICIP"
        pe = df[df[col].astype(str).str.startswith("26")]
        n = pe[col].nunique()
        return Resultado(
            "SINAN (PySUS)",
            True,
            f"dengue {ano}: {len(pe):,} notificações em PE",
            f"{n}/185",
        )
    except Exception as e:
        return Resultado("SINAN (PySUS)", False, _erro(e))


def sonda_catalogo_saude() -> Resultado:
    """Confere os datasets do catálogo Saúde SEM baixá-los.

    ATENÇÃO: chamar `pysus.sisagua()` ou `pysus.bnafar()` sem argumentos NÃO
    lista recursos — baixa a base nacional inteira. Na primeira execução deste
    spike, `pysus.sisagua()` trouxe 5,7 GB de CSV e quase encheu o disco. Uma
    sonda precisa ser barata por construção, então aqui apenas verificamos que
    os helpers existem; a ingestão de verdade tem de filtrar por UF e ano ANTES
    de materializar qualquer coisa.
    """
    config.preparar_pysus()
    try:
        import pysus
    except ImportError:
        return Resultado("Catálogo Saúde (PySUS)", False, "não instalado")
    achados = [n for n in ("sisagua", "bnafar", "arboviroses") if hasattr(pysus, n)]
    return Resultado(
        "Catálogo Saúde (PySUS)",
        bool(achados),
        f"helpers disponíveis: {', '.join(achados)} (não baixados)",
    )


SONDAS = [
    sonda_ibge_localidades,
    sonda_ibge_populacao,
    sonda_ibge_ipca,
    sonda_ibge_malhas,
    sonda_transparencia,
    sonda_pncp,
    sonda_compras_gov,
    sonda_snis,
    sonda_dados_gov,
    sonda_sinan,
    sonda_catalogo_saude,
]


def rodar() -> list[Resultado]:
    out = []
    for s in SONDAS:
        try:
            out.append(s())
        except Exception as e:  # sonda nunca derruba o spike
            out.append(Resultado(s.__name__, False, _erro(e)))
    return out

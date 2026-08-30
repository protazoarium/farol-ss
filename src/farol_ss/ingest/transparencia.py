"""Ingestão do Portal da Transparência — camada L1 (repasse federal).

O endpoint `/transferencias` (fundo a fundo, repasse ao ente) exige nível de
acesso gov.br elevado e responde **HTTP 403** com a chave gratuita. O que a
chave livre acessa são as **transferências sociais federais por município**,
geolocalizadas por `codigoIbge` — dinheiro federal que chega à população do
território. É uma L1 *parcial* e é assim documentada.

Programas usados (a rede de proteção estrutural, competência de **junho** de
cada ano):

- Bolsa Família / Auxílio Brasil / Novo Bolsa Família — o mesmo programa sob
  três nomes conforme o ano (`_PROGRAMA_BF`).
- BPC — Benefício de Prestação Continuada (idoso e pessoa com deficiência).

O **Auxílio Emergencial** (2020–2021) é deliberadamente **excluído**: é um
programa emergencial de COVID que não existe mais e cujo valor mensal chega a
ser 15× o da Bolsa Família, o que inviabilizaria a comparação entre anos.
"""

from __future__ import annotations

import time

import httpx
import pandas as pd

from farol_ss import config
from farol_ss.ingest.base import Fetcher, Proveniencia, _agora, registrar, sha256
from farol_ss.io import duck
from farol_ss.io import municipios as M

_BASE = "https://api.portaldatransparencia.gov.br/api-de-dados"
_MES = "06"  # competência mensal: junho (sem 13º, sem efeitos de fim de ano)
# A chave gratuita permite ~90 req/min (6h–24h), MAS volume alto sustentado faz
# a API BLOQUEAR a chave (redireciona 302 para /bloqueio-acesso) por algumas
# horas. Pausa conservadora (~40 req/min) para não disparar o bloqueio; a
# coleta completa leva ~40 min e é retomável.
_PAUSA_S = 1.5

# nome do endpoint do programa "Bolsa Família" conforme o ano
_PROGRAMA_BF = {
    2020: "bolsa-familia-por-municipio",
    2021: "bolsa-familia-por-municipio",
    2022: "auxilio-brasil-por-municipio",
    2023: "novo-bolsa-familia-por-municipio",
    2024: "novo-bolsa-familia-por-municipio",
}
_PROGRAMAS_FALLBACK = [
    "bolsa-familia-por-municipio",
    "auxilio-brasil-por-municipio",
    "novo-bolsa-familia-por-municipio",
]


class ChaveBloqueada(RuntimeError):
    """A API redirecionou para /bloqueio-acesso — chave bloqueada por horas."""


def _get_com_limite(f: Fetcher, url: str, **params) -> httpx.Response:
    """GET com pausa fixa, recuo no 403, e detecção do bloqueio de chave."""
    for tentativa in range(5):
        time.sleep(_PAUSA_S)
        r = f.client.get(url, params=params, follow_redirects=False)
        if r.status_code in (301, 302) and "bloqueio-acesso" in r.headers.get("location", ""):
            raise ChaveBloqueada(
                "chave da API bloqueada por excesso de requisições — aguarde algumas "
                "horas e rode `farol ingest-l1` de novo (a coleta é retomável)"
            )
        if r.status_code == 403:
            espera = min(90, 10 * 2**tentativa)
            print(f"      HTTP 403 — aguardando {espera}s")
            time.sleep(espera)
            continue
        return r
    r.raise_for_status()
    return r


def _soma_programa(f: Fetcher, endpoint: str, cod_ibge: str, ano: int) -> float:
    """Soma o `valor` mensal de um programa para um município-ano (competência
    junho). O endpoint pagina de 5 em 5, mas por município-mês há 1 registro."""
    total = 0.0
    pagina = 1
    while pagina <= 10:
        r = _get_com_limite(
            f, f"{_BASE}/{endpoint}", mesAno=f"{ano}{_MES}", codigoIbge=cod_ibge, pagina=pagina
        )
        r.raise_for_status()
        dados = r.json() if r.content and r.text.strip() else []
        if not dados:
            break
        total += sum(float(d.get("valor") or 0) for d in dados)
        pagina += 1
    return total


def _l1_municipio_ano(f: Fetcher, cod_ibge: str, ano: int) -> dict:
    bf_ep = _PROGRAMA_BF.get(ano, _PROGRAMAS_FALLBACK[-1])
    bolsa = _soma_programa(f, bf_ep, cod_ibge, ano)
    if bolsa == 0:  # o nome do programa pode ter mudado — tenta os outros
        for ep in _PROGRAMAS_FALLBACK:
            if ep == bf_ep:
                continue
            bolsa = _soma_programa(f, ep, cod_ibge, ano)
            if bolsa:
                break
    bpc = _soma_programa(f, "bpc-por-municipio", cod_ibge, ano)
    return {
        "cod_ibge": cod_ibge,
        "ano": ano,
        "l1_bolsa_familia_mes": bolsa,
        "l1_bpc_mes": bpc,
        "l1_transf_sociais_mes": bolsa + bpc,
    }


def ingerir_transparencia(limite: int | None = None) -> pd.DataFrame:
    if config.transparencia_key() is None:
        raise RuntimeError("PORTAL_TRANSPARENCIA_API_KEY não definida no .env")

    grade = [(c, a) for c in sorted(M.codigos()) for a in config.anos()]

    feito: set[tuple[str, int]] = set()
    existente: pd.DataFrame | None = None
    if duck.exists(config.SILVER, "transparencia"):
        existente = duck.read_silver("transparencia")
        feito = set(zip(existente["cod_ibge"], existente["ano"].astype(int)))

    pendentes = [g for g in grade if g not in feito]
    if limite is not None:
        pendentes = pendentes[:limite]
    print(
        f"  transparência: {len(grade)} município-anos, {len(feito)} já coletados, "
        f"{len(pendentes)} nesta execução"
    )

    linhas: list[dict] = []
    with Fetcher("transparencia", headers={"chave-api-dados": config.transparencia_key()}) as f:
        for i, (cod, ano) in enumerate(pendentes, 1):
            try:
                linhas.append(_l1_municipio_ano(f, cod, ano))
            except ChaveBloqueada as e:
                print(f"    ⛔ {e}")
                print(f"    parando com {len(linhas)} novos município-anos coletados")
                break
            except Exception as e:  # noqa: BLE001 — API instável não derruba a coleta
                print(f"    ⚠ {cod}/{ano}: {type(e).__name__} {str(e)[:60]}")
            if i % 50 == 0:
                print(f"    … {i}/{len(pendentes)}")

    novo = pd.DataFrame(linhas)
    out = novo if existente is None else pd.concat([existente, novo], ignore_index=True)
    path = duck.write_silver(out, "transparencia")
    registrar(
        Proveniencia(
            fonte="transparencia",
            url=f"{_BASE}/{{programa}}-por-municipio",
            coletado_em=_agora(),
            arquivo=str(path.relative_to(config.ROOT)),
            sha256=sha256(out.to_csv(index=False).encode()),
            bytes=out.memory_usage(deep=True).sum().item(),
            linhas=len(out),
            observacao=(
                "L1 PARCIAL: transferências sociais federais por município "
                "(Bolsa Família/Auxílio Brasil/Novo Bolsa Família + BPC), competência "
                "junho. /transferencias fundo a fundo segue bloqueado (HTTP 403)."
            ),
            extra={
                "municipios": out["cod_ibge"].nunique(),
                "anos": sorted(out["ano"].unique().tolist()),
            },
        )
    )
    print(f"  ✓ transparencia: {len(out)} linhas, {out['cod_ibge'].nunique()} municípios")
    return out


def rodar(limite: int | None = None) -> None:
    ingerir_transparencia(limite=limite)

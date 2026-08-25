"""Configuração central: caminhos, parâmetros do IEAS e catálogo de fontes.

Tudo que é parametrizável vive em conf/*.yml. Este módulo apenas carrega e
expõe, para que nenhum limiar ou peso apareça codificado no resto do projeto.
"""

from __future__ import annotations

import functools
import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONF = ROOT / "conf"
SEEDS = ROOT / "seeds"
DATA = ROOT / "data"
BRONZE = DATA / "bronze"
SILVER = DATA / "silver"
GOLD = DATA / "gold"
MANIFEST = DATA / "manifest.json"

MUNICIPIOS_CSV = CONF / "municipios_pe.csv"


@functools.cache
def ieas_conf() -> dict:
    return yaml.safe_load((CONF / "ieas.yml").read_text(encoding="utf-8"))


@functools.cache
def sources() -> dict:
    return yaml.safe_load((CONF / "sources.yml").read_text(encoding="utf-8"))


@functools.cache
def recorte() -> dict:
    return ieas_conf()["recorte"]


def anos() -> list[int]:
    r = recorte()
    return list(range(r["ano_inicio"], r["ano_fim"] + 1))


def transparencia_key() -> str | None:
    """Chave da API do Portal da Transparência (gratuita, login gov.br)."""
    return os.environ.get("PORTAL_TRANSPARENCIA_API_KEY") or None


PYSUS_CACHE = BRONZE / "pysus_cache"


def preparar_pysus() -> None:
    """Aponta o cache do PySUS para dentro do projeto.

    Precisa vir ANTES de `import pysus`: a biblioteca lê PYSUS_CACHEPATH no
    momento do import, e `pysus.set_cache()` chamado depois não reposiciona os
    downloads. Sem isto, os arquivos vão para ~/pysus e escapam do controle de
    espaço do projeto.
    """
    PYSUS_CACHE.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("PYSUS_CACHEPATH", str(PYSUS_CACHE))


def ensure_dirs() -> None:
    for d in (BRONZE, SILVER, GOLD):
        d.mkdir(parents=True, exist_ok=True)
    preparar_pysus()

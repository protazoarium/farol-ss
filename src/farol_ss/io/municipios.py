"""Dimensão municipal — a única fonte de verdade sobre os 185 municípios de PE.

Municípios são resolvidos SEMPRE por código IBGE de 7 dígitos, nunca por nome:
SNIS, SIOPS e DATASUS divergem na grafia (acentuação, hífen vs travessão,
"Lagoa de Itaenga" vs "Lagoa do Itaenga"). `chave_nome` existe apenas como
último recurso, para fontes que não publicam o código.
"""

from __future__ import annotations

import functools
import re
import unicodedata

import pandas as pd

from farol_ss import config


def chave_nome(nome: str) -> str:
    """Normaliza um nome de município para casamento tolerante.

    Remove acentos, pontuação e caixa: "Lagoa de Itaenga" -> "lagoadeitaenga".
    """
    s = unicodedata.normalize("NFKD", str(nome))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("¿", "-")  # artefato conhecido da API do IBGE
    return re.sub(r"[^a-z0-9]", "", s.lower())


@functools.cache
def municipios() -> pd.DataFrame:
    df = pd.read_csv(config.MUNICIPIOS_CSV, dtype={"cod_ibge": str})
    df["chave_nome"] = df["nome"].map(chave_nome)
    df["cod_ibge6"] = df["cod_ibge"].str[:6]  # DATASUS usa 6 dígitos
    return df


@functools.cache
def codigos() -> set[str]:
    return set(municipios()["cod_ibge"])


def resolve_por_codigo(serie: pd.Series) -> pd.Series:
    """Converte códigos IBGE de 6 ou 7 dígitos para o padrão de 7.

    Devolve NA para códigos que não pertencem a PE.
    """
    s = serie.astype(str).str.extract(r"(\d{6,7})", expand=False)
    mapa6 = municipios().set_index("cod_ibge6")["cod_ibge"]
    out = s.where(s.str.len() == 7, s.map(mapa6))
    return out.where(out.isin(codigos()))


def resolve_por_nome(serie: pd.Series) -> pd.Series:
    """Último recurso: casa por nome normalizado. Devolve NA se não casar."""
    mapa = municipios().set_index("chave_nome")["cod_ibge"]
    return serie.map(chave_nome).map(mapa)


def cobertura(df: pd.DataFrame, col: str = "cod_ibge") -> float:
    """Fração dos 185 municípios presentes em `df`."""
    return df[col].dropna().nunique() / len(codigos())

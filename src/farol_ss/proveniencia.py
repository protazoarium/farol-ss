"""Proveniência: cruza o catálogo de fontes (conf/sources.yml) com o
manifesto de coleta (data/manifest.json).

Uma linha por fonte, com o link para o conjunto no dados.gov.br, a licença e
— quando a fonte já foi ingerida — o total de linhas e a data da última
coleta. É a matéria-prima da página de Metodologia e do endpoint `/fontes`.
Módulo sem dependência de Streamlit de propósito: a API também usa.
"""

from __future__ import annotations

import json

import pandas as pd
import yaml

from farol_ss import config


def _resumo_coleta(manifest: dict, prefixo: str) -> dict:
    """Agrega as entradas do manifesto de uma fonte (que pode ter vários
    arquivos: pncp_4_2023, pncp_9_2024, ...) num único resumo."""
    itens = [v for k, v in manifest.items() if k == prefixo or k.startswith(prefixo + "_")]
    ok = [i for i in itens if i.get("status") == "ok"]
    if not ok:
        return {"coletado": False, "linhas": None, "coletado_em": None, "arquivos": 0}
    return {
        "coletado": True,
        "linhas": sum(i.get("linhas") or 0 for i in ok),
        "coletado_em": max((i.get("coletado_em") or "" for i in ok), default="") or None,
        "arquivos": len(ok),
    }


def tabela() -> pd.DataFrame:
    cat = yaml.safe_load((config.CONF / "sources.yml").read_text(encoding="utf-8"))
    manifest: dict = {}
    if config.MANIFEST.exists():
        manifest = json.loads(config.MANIFEST.read_text(encoding="utf-8"))

    linhas = []
    for chave, meta in cat.items():
        r = _resumo_coleta(manifest, chave)
        linhas.append(
            {
                "fonte": chave,
                "nome": meta.get("nome", chave),
                "camada": meta.get("camada", ""),
                "licenca": meta.get("licenca", ""),
                "dados_gov": meta.get("dados_gov", ""),
                "coletado": r["coletado"],
                "linhas": r["linhas"],
                "arquivos": r["arquivos"],
                "coletado_em": r["coletado_em"],
                "observacao": meta.get("observacao", ""),
            }
        )
    return pd.DataFrame(linhas)

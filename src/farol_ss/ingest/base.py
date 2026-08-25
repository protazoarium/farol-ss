"""Base da ingestão: HTTP com retry, cache em disco e registro de proveniência.

Nenhuma fonte entra no projeto sem uma entrada no manifest. É o manifest que
alimenta a página de Metodologia (requisito do edital de referenciar os
conjuntos do dados.gov.br) e que torna a coleta auditável: quem quiser
reproduzir sabe qual URL foi batida, quando, e com que hash de conteúdo.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Self

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from farol_ss import config

# Headers HTTP precisam ser ASCII — nada de acento aqui.
UA = "Farol-SS/0.1 (+open data monitor; health and sanitation spending)"
TIMEOUT = httpx.Timeout(60.0, connect=20.0)


@dataclass
class Proveniencia:
    """Registro de uma coleta. Serializado em data/manifest.json."""

    fonte: str
    url: str
    coletado_em: str
    arquivo: str | None = None
    sha256: str | None = None
    bytes: int | None = None
    linhas: int | None = None
    status: str = "ok"
    erro: str | None = None
    observacao: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


def _agora() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def carregar_manifest() -> dict[str, dict]:
    if config.MANIFEST.exists():
        return json.loads(config.MANIFEST.read_text(encoding="utf-8"))
    return {}


def registrar(prov: Proveniencia) -> None:
    """Grava (ou substitui) a entrada de proveniência da fonte."""
    config.MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    man = carregar_manifest()
    man[prov.fonte] = asdict(prov)
    config.MANIFEST.write_text(
        json.dumps(man, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )


class Fetcher:
    """Cliente HTTP com retry e cache em disco.

    O cache é o que sustenta a estratégia de snapshots: uma fonte já coletada
    não é rebaixada por uma indisponibilidade posterior (DATASUS e SNIS caem
    com frequência), então a demo não quebra.
    """

    def __init__(self, fonte: str, headers: dict[str, str] | None = None) -> None:
        self.fonte = fonte
        self.headers = {"User-Agent": UA, **(headers or {})}
        self.client = httpx.Client(timeout=TIMEOUT, headers=self.headers, follow_redirects=True)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc) -> None:
        self.client.close()

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
        reraise=True,
    )
    def get(self, url: str, **params) -> httpx.Response:
        r = self.client.get(url, params=params or None)
        # 404 não é transitório: não adianta insistir
        if r.status_code >= 500 or r.status_code == 429:
            r.raise_for_status()
        return r

    def baixar(
        self, url: str, destino: str, *, params: dict | None = None, forcar: bool = False
    ) -> Path:
        """Baixa para data/bronze/<destino>, reaproveitando o cache."""
        path = config.BRONZE / destino
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and not forcar:
            return path
        r = self.get(url, **(params or {}))
        r.raise_for_status()
        path.write_bytes(r.content)
        registrar(
            Proveniencia(
                fonte=self.fonte,
                url=str(r.url),
                coletado_em=_agora(),
                arquivo=str(path.relative_to(config.ROOT)),
                sha256=sha256(r.content),
                bytes=len(r.content),
            )
        )
        return path

    def paginar(
        self,
        url: str,
        *,
        params: dict,
        pagina_param: str = "pagina",
        inicio: int = 1,
        limite_paginas: int = 500,
        pausa: float = 0.2,
    ) -> list[dict]:
        """Percorre um endpoint paginado até esgotar os resultados."""
        itens: list[dict] = []
        for p in range(inicio, inicio + limite_paginas):
            r = self.get(url, **{**params, pagina_param: p})
            if r.status_code == 404:
                break
            r.raise_for_status()
            lote = r.json()
            if isinstance(lote, dict):
                lote = lote.get("data") or lote.get("items") or lote.get("resultado") or []
            if not lote:
                break
            itens.extend(lote)
            time.sleep(pausa)
        return itens

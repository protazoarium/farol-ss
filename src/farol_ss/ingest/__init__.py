"""Ingestão: orquestradores para baixar dados de cada fonte."""

from farol_ss.ingest import ibge, pncp, sinan

__all__ = ["ibge", "pncp", "sinan"]

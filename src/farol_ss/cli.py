"""CLI do Farol-SS: farol spike | ingest | silver | gold | ieas."""

from __future__ import annotations

import numpy as np
import typer
from rich.console import Console
from rich.table import Table

from farol_ss import config

app = typer.Typer(help="Farol da Saúde & Saneamento — pipeline de dados", no_args_is_help=True)
console = Console()


@app.command()
def spike() -> None:
    """Sonda cada fonte federal e reporta o que está realmente disponível."""
    from farol_ss.ingest import spike as sp

    config.ensure_dirs()
    console.print("[bold]Sondando fontes federais…[/bold] (pode levar ~1 min)\n")
    resultados = sp.rodar()

    t = Table(show_header=True, header_style="bold")
    t.add_column("Fonte")
    t.add_column("")
    t.add_column("Detalhe")
    t.add_column("Cobertura")
    for r in resultados:
        t.add_row(
            r.fonte,
            "[green]OK[/green]" if r.ok else "[red]FALHA[/red]",
            r.detalhe,
            r.cobertura,
        )
    console.print(t)

    ok = sum(r.ok for r in resultados)
    console.print(f"\n[bold]{ok}/{len(resultados)}[/bold] fontes acessíveis.")
    if ok < len(resultados):
        console.print(
            "[yellow]Fontes em falha exigem ajuste de escopo do IEAS ou coleta manual.[/yellow]"
        )


@app.command()
def ingest() -> None:
    """Baixa todas as fontes para data/bronze (idempotente)."""
    from farol_ss.ingest import (
        cadunico,
        ibge,
        ibge_saneamento,
        pncp,
        sinan,
        siops,
        transparencia,
    )

    config.ensure_dirs()
    console.print("[bold]Ingestão — Etapa 3[/bold]")
    console.print("Rodando módulos de ingestão...")
    try:
        console.print("[cyan]• IBGE[/cyan] (pop, IPCA, malhas)")
        ibge.rodar()
        console.print("[cyan]• IBGE saneamento[/cyan] (Censo 2022 — água/esgoto/lixo)")
        try:
            ibge_saneamento.rodar()
        except Exception as e:  # noqa: BLE001 — não derruba a ingestão
            console.print(f"  [yellow]⚠ Saneamento indisponível: {type(e).__name__}[/yellow]")
        console.print("[cyan]• SINAN[/cyan] (agravos notificáveis)")
        sinan.rodar()
        console.print("[cyan]• PNCP[/cyan] (contratações municipais)")
        pncp.rodar()
        console.print("[cyan]• SIOPS[/cyan] (execução própria em saúde — TabNet)")
        try:
            siops.rodar()
        except Exception as e:  # noqa: BLE001 — TabNet instável não derruba a ingestão
            console.print(f"  [yellow]⚠ SIOPS indisponível: {type(e).__name__}[/yellow]")
        console.print("[cyan]• CadÚnico[/cyan] (vulnerabilidade — SAGI/MDS)")
        try:
            cadunico.rodar()
        except Exception as e:  # noqa: BLE001 — SAGI fora do ar não derruba a ingestão
            console.print(f"  [yellow]⚠ CadÚnico indisponível: {type(e).__name__}[/yellow]")
        console.print(
            "[cyan]• Portal da Transparência[/cyan] (L1 parcial — transf. sociais; ~20 min)"
        )
        try:
            transparencia.rodar()
        except Exception as e:  # noqa: BLE001 — API instável/sem chave não derruba a ingestão
            console.print(f"  [yellow]⚠ Transparência indisponível: {type(e).__name__}[/yellow]")
        console.print("[green]✓ Ingestão concluída[/green]")
    except Exception as e:
        console.print(f"[red]✗ Erro: {e}[/red]", highlight=False)
        raise


@app.command(name="ingest-l1")
def ingest_l1(
    limite: int = typer.Option(None, help="teto de município-anos novos nesta execução"),
) -> None:
    """Baixa a camada L1 parcial (transferências sociais federais) do Portal da
    Transparência. Retomável: pula o que já está em `silver/transparencia.parquet`.
    São 925 município-anos (~2 chamadas cada); a coleta completa leva ~20 min."""
    from farol_ss.ingest import transparencia

    config.ensure_dirs()
    transparencia.rodar(limite=limite)
    console.print("[green]✓ L1 (Transparência) concluído[/green]")


@app.command(name="ingest-itens")
def ingest_itens(
    limite: int = typer.Option(None, help="teto de contratações novas nesta execução"),
) -> None:
    """Baixa os itens (com preço unitário) das contratações de saúde do PNCP.

    Alimenta o detector 3 (sobrepreço). Retomável: pula o que já está em
    `silver/pncp_itens.parquet`. São ~800 contratações de saúde; sem `--limite`
    a coleta completa leva alguns minutos (o PNCP é lento).
    """
    from farol_ss.ingest import pncp_itens

    config.ensure_dirs()
    pncp_itens.rodar(limite=limite)
    console.print("[green]✓ Itens do PNCP concluídos[/green]")


@app.command()
def silver() -> None:
    """Consolida os arquivos por fonte em tabelas únicas por domínio."""
    from farol_ss.transform import silver_epidemiologia, silver_pncp

    console.print("[cyan]• Epidemiologia[/cyan] (consolidando sinan_*.parquet)")
    silver_epidemiologia.rodar()
    console.print("[cyan]• PNCP[/cyan] (consolidando pncp_*.parquet)")
    silver_pncp.rodar()
    console.print("[green]✓ Silver concluído[/green]")


@app.command()
def gold() -> None:
    """Monta o fato município × ano (grão único do projeto)."""
    from farol_ss.transform import gold_municipio_ano

    gold_municipio_ano.rodar()
    console.print("[green]✓ Gold concluído[/green]")


@app.command()
def ieas() -> None:
    """Calcula o IEAS e os alertas a partir do gold.

    Necessidade = epidemiológico (SINAN) + saneamento (Censo 2022) +
    vulnerabilidade (CadÚnico). Alocação = L1 parcial (Transparência) + L2
    (SIOPS) + L3 (PNCP). Município-ano abaixo da cobertura mínima de
    `conf/ieas.yml` (ainda comum onde falta L1 ou L3 no PNCP) sai cinza —
    a regra do cinza, não um bug.
    """
    from farol_ss.index import anomalies
    from farol_ss.index.ieas import calcular_ieas
    from farol_ss.index.normalize import rank_percentil
    from farol_ss.io import duck

    df = duck.read_gold("fato_municipio_ano")

    # Único subíndice de necessidade disponível hoje: epidemiológico, a
    # partir das taxas por 100 mil hab. já calculadas no gold. Cada taxa
    # normalizada por rank percentil e combinada com pesos iguais — uma
    # aproximação até os pesos de conf/ieas.yml (arboviroses vs. veiculação
    # hídrica) poderem ser aplicados por agravo individualmente.
    taxa_cols = [c for c in df.columns if c.startswith("taxa_")]
    if taxa_cols:
        ranks = df[taxa_cols].apply(rank_percentil)
        df["sub_epidemiologico"] = ranks.mean(axis=1)
    else:
        df["sub_epidemiologico"] = np.nan

    # Subíndice de vulnerabilidade: rank percentil da taxa de famílias em
    # extrema pobreza (CadÚnico), calculada no gold. Mesma forma do epi.
    if "extrema_pobreza_por_mil_hab" in df.columns:
        df["sub_vulnerabilidade"] = rank_percentil(df["extrema_pobreza_por_mil_hab"])
    else:
        df["sub_vulnerabilidade"] = np.nan

    # Subíndice de saneamento: rank percentil do déficit ponderado
    # (água/esgoto/lixo) do Censo 2022, já calculado no gold. Déficit maior =
    # necessidade maior, então o rank é direto.
    if "sub_saneamento_bruto" in df.columns:
        df["sub_saneamento"] = rank_percentil(df["sub_saneamento_bruto"])
    else:
        df["sub_saneamento"] = np.nan

    for col in (
        "l1_per_capita",
        "l2_per_capita",
        "l3_per_capita",
    ):
        if col not in df.columns:
            # np.nan (float), não pd.NA: pd.NA produz coluna dtype=object e
            # gera FutureWarning de downcasting no fillna de normalize.py
            df[col] = np.nan

    out = calcular_ieas(df)
    duck.write_gold(out, "ieas")

    cobertos = out["farol"].ne("cinza").sum()
    console.print(
        f"  ✓ IEAS calculado para {cobertos}/{len(out)} município-anos (resto: cinza, cobertura insuficiente)"
    )

    # Detectores de anomalia. O detector 1 (desalinhamento) roda sobre o IEAS;
    # o 4 (desabastecimento) cruza as taxas do gold com o objeto das compras do
    # PNCP; o 3 (sobrepreço) usa os itens do PNCP com preço unitário. Cada fonte
    # ausente vira `None` e o detector correspondente devolve tabela vazia.
    compras = duck.read_silver("pncp") if duck.exists(config.SILVER, "pncp") else None
    itens = duck.read_silver("pncp_itens") if duck.exists(config.SILVER, "pncp_itens") else None
    alertas = anomalies.rodar(out, out, compras, itens)
    if not alertas.empty:
        duck.write_gold(alertas, "alertas")
        por_tipo = alertas["tipo"].value_counts().to_dict()
        console.print(f"  ✓ {len(alertas)} alertas: {por_tipo}")

    console.print("[green]✓ IEAS concluído[/green]")


if __name__ == "__main__":
    app()

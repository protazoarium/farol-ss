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
    from farol_ss.ingest import ibge, pncp, sinan

    config.ensure_dirs()
    console.print("[bold]Ingestão — Etapa 3[/bold]")
    console.print("Rodando módulos de ingestão...")
    try:
        console.print("[cyan]• IBGE[/cyan] (pop, IPCA, malhas)")
        ibge.rodar()
        console.print("[cyan]• SINAN[/cyan] (agravos notificáveis)")
        sinan.rodar()
        console.print("[cyan]• PNCP[/cyan] (contratações municipais)")
        pncp.rodar()
        console.print("[green]✓ Ingestão concluída[/green]")
    except Exception as e:
        console.print(f"[red]✗ Erro: {e}[/red]", highlight=False)
        raise


@app.command()
def silver() -> None:
    """Consolida os arquivos por fonte em tabelas únicas por domínio."""
    from farol_ss.transform import silver_epidemiologia

    console.print("[cyan]• Epidemiologia[/cyan] (consolidando sinan_*.parquet)")
    silver_epidemiologia.rodar()
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

    O eixo de Alocação (L1+L2+L3) e os subíndices de saneamento/
    vulnerabilidade ainda não têm fonte ingerida (ver docs/spike-fontes.md) —
    por isso, hoje, a cobertura de quase todo município fica abaixo do
    limiar em conf/ieas.yml e o farol sai cinza para a maioria. Isso é a
    regra do cinza funcionando como projetada, não um bug: o comando já
    prova a canalização inteira (gold → normalização → IEAS → alertas) e
    passa a produzir cor de verdade assim que SNIS/SIOPS/Transparência
    destravarem.
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

    for col in (
        "sub_saneamento",
        "sub_vulnerabilidade",
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

    alertas = anomalies.detectar_desalinhamento_estrutural(out)
    if not alertas.empty:
        duck.write_gold(alertas, "alertas")
        console.print(f"  ✓ {len(alertas)} alertas de desalinhamento estrutural")

    console.print("[green]✓ IEAS concluído[/green]")


if __name__ == "__main__":
    app()

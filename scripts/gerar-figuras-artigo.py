"""Gera as Figuras 1–4 do manuscrito em docs/artigo-revista/figuras/ (PNG 300 dpi + SVG).

Uso: uv run --extra figuras --extra pipeline python scripts/gerar-figuras-artigo.py
Pré-requisitos: `farol ieas` e `farol sensibilidade` já rodados. Só lê o gold e os CSV de
`docs/artigo-revista/resultados/`; nenhum número é digitado à mão.
"""
from __future__ import annotations

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch

from farol_ss import config
from farol_ss.config import ieas_conf, pesos_alocacao_efetivos
from farol_ss.io import duck

OUT = config.ROOT / "docs" / "artigo-revista" / "figuras"
RES = config.ROOT / "docs" / "artigo-revista" / "resultados"
COR = {"vermelho": "#c62828", "amarelo": "#ef6c00", "verde": "#00897b", "azul": "#1565c0", "cinza": "#9e9e9e"}
ROT = {"vermelho": "Vermelho (gap ≤ −0,33)", "amarelo": "Amarelo", "verde": "Verde (alinhado)",
       "azul": "Azul (gap ≥ +0,33)", "cinza": "Sem índice"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False})


def salvar(fig, nome):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{nome}.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT / f"{nome}.svg", bbox_inches="tight")
    plt.close(fig)
    print("✓", nome)


def fig1_diagrama():
    conf = ieas_conf()
    pn, pa = conf["necessidade"]["pesos"], pesos_alocacao_efetivos()
    fig, ax = plt.subplots(figsize=(10, 5.2))
    ax.set_xlim(0, 100); ax.set_ylim(0, 56); ax.axis("off")

    def caixa(x, y, w, h, txt, fc="#ffffff", ec="#1257a8", fs=8, bold=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1", fc=fc, ec=ec, lw=1.2))
        ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal")

    def seta(x1, y1, x2, y2):
        ax.annotate("", (x2, y2), (x1, y1), arrowprops={"arrowstyle": "-|>", "color": "#555", "lw": 1})

    ax.text(14, 54, "Fontes abertas", ha="center", fontweight="bold")
    ax.text(47, 54, "Subíndices (ranque por ano)", ha="center", fontweight="bold")
    ax.text(75, 54, "Eixos", ha="center", fontweight="bold")
    ax.text(93, 54, "Resultado", ha="center", fontweight="bold")
    fontes_n = [("SINAN + SIH-SUS", 38), ("Censo 2022 (IBGE)", 29), ("CadÚnico (SAGI)", 20)]
    subs_n = [(f"Epidemiológico  {pn['epidemiologico']:.2f}", 38), (f"Saneamento  {pn['saneamento']:.2f}", 29),
              (f"Vulnerabilidade  {pn['vulnerabilidade']:.2f}", 20)]
    for (f, y), (s, _) in zip(fontes_n, subs_n):
        caixa(2, y, 24, 6, f, fc="#e8f0fb"); caixa(34, y, 26, 6, s); seta(26.6, y + 3, 33.4, y + 3); seta(60.6, y + 3, 67, 29 + 3 + (y - 29) * 0.3)
    caixa(67, 28, 17, 8, "Eixo N\nNecessidade", fc="#1257a8", ec="#1257a8", fs=9, bold=True)
    ax.texts[-1].set_color("white")
    fontes_a = [("Transparência (L1)", 9), ("SIOPS (L2)", 2)]
    subs_a = [(f"L1  {pa['l1_repasse_federal']:.2f}", 9), (f"L2  {pa['l2_execucao_propria']:.2f}", 2)]
    for (f, y), (s, _) in zip(fontes_a, subs_a):
        caixa(2, y, 24, 5, f, fc="#e8f0fb"); caixa(34, y, 26, 5, s); seta(26.6, y + 2.5, 33.4, y + 2.5); seta(60.6, y + 2.5, 67, 9)
    caixa(67, 4, 17, 8, "Eixo A\nAlocação", fc="#1257a8", ec="#1257a8", fs=9, bold=True)
    ax.texts[-1].set_color("white")
    caixa(34, 47.5, 26, 4, "L3 (PNCP): fora do índice\n(sensibilidade e alertas)", fc="#f4f4f4", ec="#9e9e9e", fs=7)
    caixa(88, 16, 11, 14, "gap = A − N\n\nsemáforo\n5 cores", fc="#fff4db", ec="#ef6c00", fs=8)
    seta(84.6, 32, 88, 25); seta(84.6, 8, 88, 21)
    ax.text(50, 0.2, "Ranque percentil calculado separadamente em cada ano (185 municípios).", ha="center", fontsize=7.5, color="#444")
    return fig


def fig2_mapa(df):
    mal = pd.read_parquet(config.BRONZE / "ibge_malhas.parquet")
    g = gpd.GeoDataFrame(mal.assign(geometry=gpd.GeoSeries.from_wkb(mal["geometry"])), geometry="geometry")
    fig, axs = plt.subplots(2, 3, figsize=(10.5, 4.9))
    axs = axs.ravel()
    axs[5].axis("off")
    for ax, ano in zip(axs, range(2020, 2025)):
        d = g.merge(df[df.ano == ano][["cod_ibge", "farol"]], on="cod_ibge", how="left")
        d.plot(ax=ax, color=d["farol"].map(COR).fillna("#ffffff"), edgecolor="white", linewidth=0.15)
        x0, y0, x1, y1 = g[g.cod_ibge != "2605459"].total_bounds  # sem Fernando de Noronha (ilha distante)
        ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal")
        ax.set_title(str(ano), fontsize=10); ax.axis("off")
    axs[5].legend(handles=[Line2D([], [], marker="s", ls="", ms=10, color=COR[k], label=ROT[k]) for k in COR],
                  loc="center", frameon=False, fontsize=10, title="Fernando de Noronha (ilha) não aparece no mapa;\nfica sem índice em todos os anos.", title_fontsize=8)
    salvar(fig, "fig2_mapa")


def fig3_dispersao(df):
    d = df[(df.ano == 2024) & df.gap.notna()]
    fig, ax = plt.subplots(figsize=(5.6, 5.4))
    peq = d.populacao < 10_000
    for k, c in COR.items():
        for m, mk, rot in ((~peq, "o", "≥ 10 mil hab."), (peq, "^", "< 10 mil hab.")):
            s = d[(d.farol == k) & m]
            ax.scatter(s.necessidade_rank, s.alocacao_rank, c=c, marker=mk, s=26, alpha=0.85, lw=0)
    ax.plot([0, 1], [0, 1], color="#333", lw=0.8, ls="--")
    ax.set_xlabel("Necessidade (ranque percentil, 2024)"); ax.set_ylabel("Alocação (ranque percentil, 2024)")
    ax.set_xlim(-0.02, 1.02); ax.set_ylim(-0.02, 1.02)
    ax.legend(handles=[Line2D([], [], marker="o", ls="", color="#555", label="≥ 10 mil hab."),
                       Line2D([], [], marker="^", ls="", color="#555", label="< 10 mil hab."),
                       Line2D([], [], color="#333", ls="--", label="gap = 0")], frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3)
    salvar(fig, "fig3_dispersao")


def fig4_sensibilidade():
    v = pd.read_csv(RES / "variantes.csv")
    dz = pd.read_csv(RES / "dirichlet_resumo.csv").set_index("medida")
    pca = pd.read_csv(RES / "pca.csv").iloc[0]
    def limpa(t):
        for a, b in (("Pesos: ", ""), ("Pesos iguais nos eixos", "Pesos iguais nos dois eixos"), ("l1_repasse_federal", "L1"),
                     ("l2_execucao_propria", "L2"), ("epidemiologico", "epidemiológico"), ("Interno", "interno"),
                     ("externo", "externo"), (" subíndice", " subíndice"), ("0.", "0,")):
            t = t.replace(a, b)
        return t
    linhas = [(limpa(f"{r.grupo}: {r.variante}") if r.grupo != "Pesos" else "Pesos: " + limpa(r.variante), r.muda_cor_pct, r.grupo) for r in v.itertuples()]
    linhas.append(("Agregação de N: 1º componente principal", pca["pca_muda_cor_pct"], "Agregação"))
    linhas.append(("Pesos: mediana de 1.000 sorteios (Dirichlet)", 100 - dz.loc["mantem_cor_pct", "mediana"], "Pesos"))
    linhas = sorted(linhas, key=lambda t: t[1])
    paleta = {"Normalização": "#c62828", "Pesos": "#1257a8", "Limiares": "#00897b", "Eixo A": "#ef6c00", "Eixo N": "#7b1fa2", "Agregação": "#555555"}
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.barh([l[0] for l in linhas], [l[1] for l in linhas], color=[paleta[l[2]] for l in linhas])
    ax.set_xlabel("Município-anos que mudam de cor frente ao caso-base (%)")
    ax.tick_params(axis="y", labelsize=7)
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=c) for c in paleta.values()], labels=list(paleta), frameon=False, loc="lower right")
    salvar(fig, "fig4_sensibilidade")


def main():
    df = duck.read_gold("ieas")
    f = fig1_diagrama(); salvar(f, "fig1_diagrama")
    fig2_mapa(df); fig3_dispersao(df); fig4_sensibilidade()


if __name__ == "__main__":
    main()

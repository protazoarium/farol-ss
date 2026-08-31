#!/usr/bin/env python3
"""Gera os gráficos do pôster a partir de revisao/_farol_dados.json
(extraído de data/gold/ieas.parquet)."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).parent
D = json.loads((HERE / "revisao" / "_farol_dados.json").read_text(encoding="utf-8"))
OUT = HERE / "assets"
OUT.mkdir(exist_ok=True)

COR = {"vermelho": "#c62828", "amarelo": "#ef6c00", "verde": "#00897b",
       "azul": "#1565c0", "cinza": "#9e9e9e"}
ROT = {"vermelho": "Necessidade não\natendida", "amarelo": "Subalocação\nleve",
       "verde": "Alocação\nalinhada", "azul": "Alocação acima\nda necessidade",
       "cinza": "Sem dado"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12,
                     "axes.edgecolor": "#8a8a86", "axes.linewidth": .8,
                     "svg.fonttype": "none"})


def salvar(fig, nome):
    fig.savefig(OUT / nome, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("  ->", nome)


# 1 — distribuição do farol (todos os anos)
ordem = ["verde", "azul", "amarelo", "vermelho", "cinza"]
vals = [D["farol_total"].get(k, 0) for k in ordem]
fig, ax = plt.subplots(figsize=(6.4, 3.1))
b = ax.barh([ROT[k] for k in ordem][::-1], vals[::-1],
            color=[COR[k] for k in ordem][::-1])
ax.bar_label(b, padding=4, fontsize=12, fontweight="bold")
ax.set_xlim(0, max(vals) * 1.18)
ax.set_xlabel("município-anos (2020–2024; total = 925)")
ax.spines[["top", "right"]].set_visible(False)
ax.set_title("Distribuição do farol — Pernambuco, 2020–2024", fontsize=12.5,
             fontweight="bold", loc="left")
salvar(fig, "fig1_farol_dist.png")

# 2 — farol por ano (barras empilhadas)
anos = sorted(D["farol_por_ano"])
fig, ax = plt.subplots(figsize=(6.4, 3.3))
base = [0] * len(anos)
for k in ["vermelho", "amarelo", "verde", "azul", "cinza"]:
    v = [D["farol_por_ano"][a][k] for a in anos]
    ax.bar(anos, v, bottom=base, color=COR[k], width=.62,
           label=k.capitalize())
    base = [b + x for b, x in zip(base, v)]
ax.set_ylabel("nº de municípios")
ax.set_title("Farol por ano", fontsize=12.5, fontweight="bold", loc="left")
ax.legend(ncol=5, fontsize=9.5, frameon=False, loc="upper center",
          bbox_to_anchor=(.5, -.12))
ax.spines[["top", "right"]].set_visible(False)
salvar(fig, "fig2_farol_ano.png")

# 3 — dispersão necessidade x alocação, 2024 (o IEAS visto de cima)
s = D["scatter_2024"]
fig, ax = plt.subplots(figsize=(5.2, 5.0))
for k in ["cinza", "verde", "azul", "amarelo", "vermelho"]:
    xs = [x for x, f in zip(s["nec"], s["farol"]) if f == k]
    ys = [y for y, f in zip(s["aloc"], s["farol"]) if f == k]
    ax.scatter(xs, ys, s=34, c=COR[k], edgecolors="white", linewidths=.5,
               label=k.capitalize(), zorder=3)
ax.plot([0, 1], [0, 1], "--", color="#545c6b", lw=1.1, zorder=2)
ax.fill_between([0.33, 1.33], [0, 1], [-1, 0], color="#c62828", alpha=.05, zorder=1)
ax.text(.72, .30, "subalocação\n(vermelho/amarelo)", fontsize=9, color="#c62828", ha="center")
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_xlabel("Necessidade — ranque percentil (PE)")
ax.set_ylabel("Alocação — ranque percentil (PE)")
ax.set_title("Necessidade × alocação — PE, 2024", fontsize=12.5,
             fontweight="bold", loc="left")
ax.legend(fontsize=9, frameon=False, loc="lower right")
ax.set_aspect("equal")
salvar(fig, "fig3_scatter_2024.png")

# 4 — alertas de desabastecimento por ano
da = D["alertas_desab_ano"]
anos2 = sorted(int(a) for a in da)
fig, ax = plt.subplots(figsize=(6.2, 2.8))
bb = ax.bar([str(a) for a in anos2], [da[str(a)] for a in anos2],
            color="#1257a8", width=.6)
ax.bar_label(bb, padding=3, fontweight="bold")
ax.set_ylabel("alertas")
ax.set_title("Suspeita de desabastecimento de insumos, por ano (570)",
             fontsize=11.5, fontweight="bold", loc="left", pad=12)
ax.spines[["top", "right"]].set_visible(False)
salvar(fig, "fig4_desabastecimento.png")

print("gráficos em", OUT)

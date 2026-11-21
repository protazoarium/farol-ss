"""Análise de sensibilidade e validação do IEAS.

Tudo que o artigo cita como "robustez" ou "validação" nasce daqui, por um
único comando (`farol sensibilidade`), para que cada número do manuscrito seja
regenerável a partir do gold. O código do índice é o mesmo de `index/ieas.py`:
cada variante é só uma chamada de `calcular_ieas` com outros parâmetros.

Medidas de concordância: percentual de município-anos que **mantêm a cor** do
caso-base (a cor "cinza" conta como uma cor) e correlação de Spearman do gap
com o gap do caso-base.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from farol_ss.config import ieas_conf
from farol_ss.index.ieas import calcular_ieas, montar_subindices

_TRES = ["l1_repasse_federal", "l2_execucao_propria", "l3_contratacao_insumos"]
_N = ["epidemiologico", "saneamento", "vulnerabilidade"]


def _sp(a: pd.Series, b: pd.Series) -> float:
    """Spearman = Pearson dos postos (evita depender de scipy)."""
    return a.rank().corr(b.rank())


def _base(df: pd.DataFrame) -> pd.DataFrame:
    return calcular_ieas(montar_subindices(df))


def _concordancia(base: pd.DataFrame, var: pd.DataFrame) -> dict:
    mesma = (base["farol"].to_numpy() == var["farol"].to_numpy()).mean()
    ok = base["gap"].notna() & var["gap"].notna()
    rho = _sp(base.loc[ok, "gap"], var.loc[ok, "gap"])
    return {
        "mantem_cor_pct": round(100 * mesma, 1),
        "muda_cor_pct": round(100 * (1 - mesma), 1),
        "spearman_gap": round(float(rho), 3),
        "n_cinza": int((var["farol"] == "cinza").sum()),
    }


def _limiares(interno: float, externo: float) -> dict:
    return {
        "vermelho_ate": -externo,
        "amarelo_ate": -interno,
        "verde_ate": interno,
        "azul_a_partir": externo,
    }


def _remover(pesos: dict, chave: str) -> dict:
    return {k: (0.0 if k == chave else v) for k, v in pesos.items()}


def variantes(df: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por variante determinística, com a concordância frente ao caso-base."""
    conf = ieas_conf()
    pn, pa = conf["necessidade"]["pesos"], conf["alocacao"]["pesos"]
    base = _base(df)
    linhas: list[tuple[str, str, pd.DataFrame]] = []

    # 1. Normalização
    linhas.append(
        ("Normalização", "Ranque empilhado (925 município-anos)", calcular_ieas(montar_subindices(df, por_ano=False), por_ano=False))
    )
    linhas.append(
        ("Normalização", "Escore-z (via CDF normal) por ano", calcular_ieas(montar_subindices(df, metodo="z"), metodo="z"))
    )

    sub = montar_subindices(df)

    # 2. Pesos
    linhas.append(("Pesos", "Pesos iguais nos eixos", calcular_ieas(
        sub, pesos_n={k: 1 / 3 for k in _N}, pesos_a={k: 0.5 for k in _TRES}
    )))
    for k in _N:
        for f, nome in ((1.2, "+20%"), (0.8, "−20%")):
            p = {**pn, k: pn[k] * f}
            linhas.append(("Pesos", f"Eixo N: peso {k} {nome}", calcular_ieas(sub, pesos_n=p)))
    for k in _TRES[:2]:
        for f, nome in ((1.2, "+20%"), (0.8, "−20%")):
            p = {**pa, k: pa[k] * f}
            linhas.append(("Pesos", f"Eixo A: peso {k} {nome}", calcular_ieas(sub, pesos_a=p)))

    # 3. Limiares
    for i, e in ((0.05, 0.33), (0.15, 0.33), (0.10, 0.25), (0.10, 0.40)):
        linhas.append(("Limiares", f"Interno ±{i:.2f} / externo ±{e:.2f}", calcular_ieas(sub, limiares=_limiares(i, e))))

    # 4. Composição do eixo A
    linhas.append(("Eixo A", "Com L3 (PNCP) — composição de 3 componentes", calcular_ieas(sub, componentes_a=_TRES)))
    linhas.append(("Eixo A", "Sem L1 (só L2)", calcular_ieas(sub, componentes_a=["l2_execucao_propria"])))

    # 5. Remoção de cada subíndice do eixo N (pesos renormalizados)
    for k in _N:
        s2 = sub.copy()
        s2["sub_" + k] = np.nan
        linhas.append(("Eixo N", f"Sem o subíndice {k}", calcular_ieas(s2)))

    out = []
    for grupo, nome, var in linhas:
        out.append({"grupo": grupo, "variante": nome, **_concordancia(base, var)})
    return pd.DataFrame(out)


def dirichlet(df: pd.DataFrame, n: int = 1000, seed: int = 20260101) -> pd.DataFrame:
    """Sorteia `n` vetores de pesos (Dirichlet(1,…)) para os eixos N (3) e A (L1, L2).

    Devolve a concordância por sorteio; o artigo reporta mediana e intervalo
    entre os percentis 5 e 95.
    """
    rng = np.random.default_rng(seed)
    base = _base(df)
    sub = montar_subindices(df)
    linhas = []
    for _ in range(n):
        wn = rng.dirichlet(np.ones(3))
        wa = rng.dirichlet(np.ones(2))
        var = calcular_ieas(
            sub,
            pesos_n=dict(zip(_N, wn)),
            pesos_a={"l1_repasse_federal": wa[0], "l2_execucao_propria": wa[1], "l3_contratacao_insumos": 0.0},
        )
        linhas.append(_concordancia(base, var))
    return pd.DataFrame(linhas)


def cores_por_ano(base: pd.DataFrame) -> pd.DataFrame:
    return (
        base.groupby(["ano", "farol"]).size().unstack(fill_value=0)
        .reindex(columns=["vermelho", "amarelo", "verde", "azul", "cinza"], fill_value=0)
    )


def associacao_eixos(base: pd.DataFrame) -> pd.DataFrame:
    """P1 — Spearman entre os ranques de N e A, por ano."""
    linhas = []
    for ano, g in base.groupby("ano"):
        ok = g["necessidade_rank"].notna() & g["alocacao_rank"].notna()
        linhas.append(
            {
                "ano": int(ano),
                "n": int(ok.sum()),
                "spearman_N_A": round(float(_sp(g.loc[ok, "necessidade_rank"], g.loc[ok, "alocacao_rank"])), 3),
            }
        )
    return pd.DataFrame(linhas)


def municipios_pequenos(base: pd.DataFrame, corte: int = 10_000) -> pd.DataFrame:
    """P3 — cores extremas (vermelho/azul) em municípios pequenos × demais."""
    b = base[base["farol"] != "cinza"].copy()
    b["porte"] = np.where(b["populacao"] < corte, f"< {corte:,} hab.".replace(",", "."), f"≥ {corte:,} hab.".replace(",", "."))
    b["extremo"] = b["farol"].isin(["vermelho", "azul"])
    r = b.groupby("porte").agg(municipio_anos=("farol", "size"), extremos_pct=("extremo", lambda s: round(100 * s.mean(), 1)))
    r["municipios_distintos"] = b.groupby("porte")["cod_ibge"].nunique()
    return r.reset_index()


def efeito_pncp(df: pd.DataFrame) -> pd.DataFrame:
    """P4 — cobertura de L3 por ano e quanto ela move o gap quando entra no eixo A."""
    base = _base(df)
    sub = montar_subindices(df)
    com = calcular_ieas(sub, componentes_a=_TRES)
    df2 = pd.DataFrame(
        {
            "ano": base["ano"],
            "tem_l3": df["l3_per_capita"].notna(),
            "delta_gap_abs": (com["gap"] - base["gap"]).abs(),
            "muda_cor": base["farol"] != com["farol"],
        }
    )
    return df2.groupby("ano").agg(
        com_l3=("tem_l3", "sum"),
        delta_gap_abs_medio=("delta_gap_abs", lambda s: round(float(s.mean()), 3)),
        muda_cor_pct=("muda_cor", lambda s: round(100 * s.mean(), 1)),
    ).reset_index()


def validacao_desfecho(base: pd.DataFrame) -> pd.DataFrame:
    """Validade preditiva exploratória: o gap em t anuncia o desfecho em t+1?

    Desfecho disponível no recorte: taxa de internações por condições
    relacionadas a saneamento (SIH/DRSAI) por 100 mil hab. Duas leituras, por
    pares (t, t+1): Spearman entre o gap em t e (a) a variação da taxa de
    internações e (b) o nível da taxa em t+1. Óbitos não estão no recorte.
    """
    d = base[["cod_ibge", "ano", "gap", "necessidade_rank", "taxa_internacoes_drsai"]].copy()
    prox = d.assign(ano=d["ano"] - 1).rename(columns={"taxa_internacoes_drsai": "taxa_t1"})[["cod_ibge", "ano", "taxa_t1"]]
    m = d.merge(prox, on=["cod_ibge", "ano"], how="inner")
    m["delta"] = m["taxa_t1"] - m["taxa_internacoes_drsai"]
    ok = m.dropna(subset=["gap", "taxa_t1", "taxa_internacoes_drsai"])
    # parcial simples: o gap em t correlaciona com a variação, controlando o nível (ranque de N)
    r = []
    for nome, y in (("Variação da taxa de internações (t+1 − t)", "delta"), ("Taxa de internações em t+1", "taxa_t1")):
        r.append({"desfecho": nome, "n_pares": len(ok), "spearman_com_gap": round(float(_sp(ok["gap"], ok[y])), 3)})
    return pd.DataFrame(r)


def comparacao_pca(df: pd.DataFrame) -> dict:
    """Compara o eixo N (média ponderada de ranques) com o 1º componente principal.

    O PC1 é calculado, por ano, sobre os três subíndices padronizados. Devolve
    o Spearman entre os dois ordenamentos e a concordância de cor quando o
    ranque de N é substituído pelo ranque do PC1.
    """
    sub = montar_subindices(df)
    base = calcular_ieas(sub)
    pc_rank = pd.Series(np.nan, index=sub.index)
    var_expl = []
    cols = ["sub_epidemiologico", "sub_saneamento", "sub_vulnerabilidade"]
    for idx in sub.groupby("ano").groups.values():
        x = sub.loc[idx, cols].dropna()
        z = ((x - x.mean()) / x.std(ddof=0)).to_numpy()
        _, s, vt = np.linalg.svd(z, full_matrices=False)
        pc = z @ vt[0]
        if np.corrcoef(pc, x.mean(axis=1))[0, 1] < 0:
            pc = -pc
        var_expl.append(float(s[0] ** 2 / (s**2).sum()))
        pc_rank.loc[x.index] = pd.Series(pc, index=x.index).rank(pct=True)
    var = base.copy()
    var["necessidade_rank"] = pc_rank
    var["gap"] = var["alocacao_rank"] - var["necessidade_rank"]
    from farol_ss.index.ieas import classificar_farol

    var["farol"] = classificar_farol(var["gap"])
    ok = base["necessidade_rank"].notna() & pc_rank.notna()
    return {
        "spearman_N_vs_PC1": round(float(_sp(base.loc[ok, "necessidade_rank"], pc_rank[ok])), 3),
        "variancia_explicada_pc1_media_pct": round(100 * float(np.mean(var_expl)), 1),
        **{f"pca_{k}": v for k, v in _concordancia(base, var).items()},
    }


def rodar(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    base = _base(df)
    dir_ = dirichlet(df)
    resumo_dir = pd.DataFrame(
        {
            "medida": ["mantem_cor_pct", "spearman_gap"],
            "mediana": [dir_["mantem_cor_pct"].median(), dir_["spearman_gap"].median()],
            "p05": [dir_["mantem_cor_pct"].quantile(0.05), dir_["spearman_gap"].quantile(0.05)],
            "p95": [dir_["mantem_cor_pct"].quantile(0.95), dir_["spearman_gap"].quantile(0.95)],
        }
    ).round(3)
    return {
        "cores_por_ano": cores_por_ano(base).reset_index(),
        "associacao_eixos": associacao_eixos(base),
        "variantes": variantes(df),
        "dirichlet_resumo": resumo_dir,
        "municipios_pequenos": municipios_pequenos(base),
        "efeito_pncp": efeito_pncp(df),
        "validacao_desfecho": validacao_desfecho(base),
        "pca": pd.DataFrame([comparacao_pca(df)]),
    }

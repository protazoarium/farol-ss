"""Checagem da quebra de série de L1 em 2022 (Portal da Transparência, Auxílio Brasil).

Achado: no endpoint `auxilio-brasil-por-municipio` o valor médio por família é ~R$ 160 de jan a
jun/2022 e passa a ~R$ 430 a partir de jul/2022, sem mudança no nº de famílias. A competência de
junho (usada em todos os anos) cai, em 2022, ANTES da quebra. Este script (1) recoleta julho/2022
(185 municípios, 1 chamada cada) e (2) mede quanto o semáforo de 2022 muda se L1 usar julho.

Uso: uv run python scripts/l1_checagem_2022.py coletar   # ~15 min, precisa de PORTAL_TRANSPARENCIA_API_KEY
     uv run python scripts/l1_checagem_2022.py analisar  # usa o CSV já coletado
Saída: docs/artigo-revista/resultados/l1_2022_julho.csv e l1_2022_sensibilidade.csv
"""
from __future__ import annotations

import csv
import sys
import time

import httpx
import pandas as pd

from farol_ss import config
from farol_ss.index.ieas import calcular_ieas, montar_subindices
from farol_ss.io import duck

RES = config.ROOT / "docs" / "artigo-revista" / "resultados"
CSV = RES / "l1_2022_julho.csv"
BASE = "https://api.portaldatransparencia.gov.br/api-de-dados"


def coletar() -> None:
    chave = config.transparencia_key()
    assert chave, "defina PORTAL_TRANSPARENCIA_API_KEY no .env"
    with open(config.CONF / "municipios_pe.csv", encoding="utf-8") as f:
        cods = [r["cod_ibge"] for r in csv.DictReader(f)]
    linhas = []
    for c in cods:
        for _ in range(3):
            r = httpx.get(f"{BASE}/auxilio-brasil-por-municipio", params={"mesAno": "202207", "codigoIbge": c, "pagina": 1},
                          headers={"chave-api-dados": chave}, timeout=40, follow_redirects=False)
            if r.status_code == 200:
                break
            time.sleep(10)
        d = r.json() if r.status_code == 200 and r.text.strip() else []
        linhas.append({"cod_ibge": c, "bf_jul_valor": sum(x["valor"] for x in d),
                       "bf_jul_familias": sum(x["quantidadeBeneficiados"] for x in d)})
        time.sleep(1.5)
    pd.DataFrame(linhas).to_csv(CSV, index=False)


def analisar() -> None:
    jul = pd.read_csv(CSV, dtype={"cod_ibge": str})
    sil = duck.read_silver("transparencia")
    sil = sil[sil.ano == 2022][["cod_ibge", "l1_bolsa_familia_mes", "l1_bpc_mes"]]
    m = sil.merge(jul, on="cod_ibge")
    m["fator"] = (m.bf_jul_valor + m.l1_bpc_mes) / (m.l1_bolsa_familia_mes + m.l1_bpc_mes)
    df = duck.read_gold("fato_municipio_ano")
    alt = df.merge(m[["cod_ibge", "fator"]], on="cod_ibge", how="left")
    alt.loc[alt.ano != 2022, "fator"] = 1.0
    alt["l1_per_capita"] = alt["l1_per_capita"] * alt["fator"].fillna(1.0)
    base = calcular_ieas(montar_subindices(df))
    var = calcular_ieas(montar_subindices(alt))
    b22, v22 = base[base.ano == 2022].reset_index(drop=True), var[var.ano == 2022].reset_index(drop=True)
    sp = lambda a, b: a.rank().corr(b.rank())
    out = pd.DataFrame([{
        "bf_jun_total_mi": round(m.l1_bolsa_familia_mes.sum() / 1e6, 1),
        "bf_jul_total_mi": round(m.bf_jul_valor.sum() / 1e6, 1),
        "razao_jul_jun": round(m.bf_jul_valor.sum() / m.l1_bolsa_familia_mes.sum(), 2),
        "familias_jul": int(m.bf_jul_familias.sum()),
        "rs_por_familia_jul": round(m.bf_jul_valor.sum() / m.bf_jul_familias.sum()),
        "spearman_l1_jun_vs_jul": round(sp(b22.l1_per_capita, v22.l1_per_capita), 3),
        "mantem_cor_2022_pct": round(100 * (b22.farol == v22.farol).mean(), 1),
        "spearman_gap_2022": round(sp(b22.gap, v22.gap), 3),
    }])
    out.to_csv(RES / "l1_2022_sensibilidade.csv", index=False)
    print(out.T.to_string())


if __name__ == "__main__":
    {"coletar": coletar, "analisar": analisar}[sys.argv[1]]()

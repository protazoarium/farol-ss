"""Detectores de gargalo e vulnerabilidade.

Do plano original (4 detectores), dois estão implementados aqui porque só
dependem de dado já disponível e testável com fixtures sintéticas:

1. Desalinhamento estrutural — trivial, deriva direto do `gap` do ieas.py.
4. Suspeita de desabastecimento — o detector mais original do projeto: liga
   incidência sustentada de um agravo (SINAN) à ausência de contratação da
   categoria de insumo correspondente (PNCP), via `seeds/agravo_insumo.yml`.

Os detectores 2 (resíduo de regressão) e 3 (preço fora da curva) do plano
ficam de fora desta versão:
- Detector 2 precisa do eixo de Alocação completo (L1+L2+L3 per capita);
  como L1 (Transparência) e L2 (SIOPS) ainda estão bloqueados (ver
  docs/spike-fontes.md), implementar agora produziria um resíduo calculado
  sobre um terço do gasto real — enganoso, não apenas incompleto.
- Detector 3 (sobrepreço) precisa de preço unitário por item de compra, mas
  o endpoint de PNCP usado (`/v1/contratacoes/publicacao`) devolve valor
  TOTAL da compra, não por item — não há como isolar "preço do larvicida"
  dali. Precisaria de outro endpoint (nível de item), não verificado nesta
  sessão.

Cada detector devolve linhas com `explicacao` em texto legível — um alerta
sem explicação não serve para auditoria cidadã.
"""

from __future__ import annotations

import pandas as pd
import yaml

from farol_ss.config import SEEDS, ieas_conf


def detectar_desalinhamento_estrutural(df_ieas: pd.DataFrame) -> pd.DataFrame:
    """Detector 1: farol vermelho é, por definição, o alerta mais direto."""
    alvo = df_ieas[df_ieas["farol"] == "vermelho"].copy()
    alvo["tipo"] = "desalinhamento_estrutural"
    alvo["severidade"] = pd.cut(
        alvo["gap"], bins=[-1.01, -0.6, -0.33], labels=["alta", "moderada"]
    ).astype(str)
    alvo["explicacao"] = alvo.apply(
        lambda r: (
            f"Necessidade no percentil {r['necessidade_rank']:.0%} de PE, mas "
            f"alocação apenas no percentil {r['alocacao_rank']:.0%} — "
            f"desalinhamento de {abs(r['gap']):.0%}."
        ),
        axis=1,
    )
    return alvo[["cod_ibge", "ano", "tipo", "severidade", "gap", "explicacao"]]


def _carregar_agravo_insumo() -> dict:
    return yaml.safe_load((SEEDS / "agravo_insumo.yml").read_text(encoding="utf-8"))


def _carregar_catmat() -> pd.DataFrame:
    import csv

    with open(SEEDS / "catmat_saude.csv", encoding="utf-8") as f:
        return pd.DataFrame(list(csv.DictReader(f)))


def _municipio_comprou_categoria(
    compras: pd.DataFrame, cod_ibge: str, ano: int, categoria: str, catmat: pd.DataFrame
) -> bool:
    """Casamento por palavra-chave entre objeto_compra e a descrição da
    categoria — heurística simples e explicável, não NLP. Uma versão futura
    pode trocar por matching mais robusto sem mudar a interface do detector.
    """
    palavras_chave = catmat[catmat["categoria"] == categoria]["descricao"].tolist()
    if not palavras_chave or "objeto_compra" not in compras.columns:
        return False

    do_municipio = compras[(compras["cod_ibge"] == cod_ibge) & (compras["ano"] == ano)]
    if do_municipio.empty:
        return False

    termos = {t.lower() for kw in palavras_chave for t in kw.split() if len(t) > 4}
    objetos = do_municipio["objeto_compra"].fillna("").str.lower()
    return objetos.apply(lambda texto: any(t in texto for t in termos)).any()


def detectar_desabastecimento(
    epidemiologia: pd.DataFrame, compras: pd.DataFrame | None
) -> pd.DataFrame:
    """Detector 4: surto sustentado sem a contratação de insumo correspondente.

    `compras` é o resultado consolidado do PNCP (cod_ibge, ano,
    objeto_compra, ...). Se `None` (ainda não ingerido), o detector devolve
    uma tabela vazia com o schema correto em vez de falhar — permite testar
    o resto do pipeline sem bloquear na dependência.
    """
    schema_vazio = pd.DataFrame(
        columns=["cod_ibge", "ano", "tipo", "severidade", "agravo", "explicacao"]
    )
    if compras is None or compras.empty:
        return schema_vazio

    agravo_insumo = _carregar_agravo_insumo()
    catmat = _carregar_catmat()
    limiar = ieas_conf()["alertas"]["desabastecimento"]["incidencia_percentil_minimo"]

    achados = []
    for agravo_cod, spec in agravo_insumo.items():
        col_taxa = f"taxa_{agravo_cod.lower()}"
        if col_taxa not in epidemiologia.columns:
            continue

        corte = epidemiologia[col_taxa].quantile(limiar)
        surto = epidemiologia[epidemiologia[col_taxa] >= corte]

        for _, row in surto.iterrows():
            comprou_algo = any(
                _municipio_comprou_categoria(compras, row["cod_ibge"], row["ano"], cat, catmat)
                for cat in spec["insumos_esperados"]
            )
            if not comprou_algo:
                achados.append(
                    {
                        "cod_ibge": row["cod_ibge"],
                        "ano": row["ano"],
                        "tipo": "suspeita_desabastecimento",
                        "severidade": "alta",
                        "agravo": spec["nome"],
                        "explicacao": (
                            f"Incidência de {spec['nome']} no percentil "
                            f"{limiar:.0%}+ de PE em {row['ano']}, mas nenhuma "
                            f"contratação de {', '.join(spec['insumos_esperados'])} "
                            f"encontrada no PNCP para o município no período."
                        ),
                    }
                )

    return pd.DataFrame(achados) if achados else schema_vazio


def rodar(df_ieas: pd.DataFrame, epidemiologia: pd.DataFrame, compras: pd.DataFrame | None):
    d1 = detectar_desalinhamento_estrutural(df_ieas)
    d4 = detectar_desabastecimento(epidemiologia, compras)
    comuns = ["cod_ibge", "ano", "tipo", "severidade", "explicacao"]
    return pd.concat([d1[comuns], d4[comuns]], ignore_index=True)

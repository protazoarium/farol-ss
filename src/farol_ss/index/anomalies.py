"""Detectores de gargalo e vulnerabilidade.

Três dos quatro detectores do plano estão implementados:

1. Desalinhamento estrutural — trivial, deriva direto do `gap` do ieas.py.
   Depende do IEAS ter cor, então hoje não produz linhas (tudo cinza).
3. Suspeita de sobrepreço — preço unitário de um item de insumo acima de
   Q3 + fator·IQR da distribuição da mesma categoria em PE. Usa
   `silver/pncp_itens.parquet` (ver `ingest/pncp_itens.py`), que puxa o preço
   por item do recurso `/v1/orgaos/{cnpj}/compras/{ano}/{seq}/itens` do PNCP —
   o recurso de consulta genérico só traz o valor total da compra.
4. Suspeita de desabastecimento — o detector mais original do projeto: liga
   incidência sustentada de um agravo (SINAN) à ausência de contratação da
   categoria de insumo correspondente (PNCP), via `seeds/agravo_insumo.yml`.

O detector 2 (resíduo de regressão robusta) fica de fora: precisa do eixo de
Alocação completo (L1+L2+L3 per capita); como L1 (Transparência) e L2 (SIOPS)
ainda estão bloqueados (ver docs/spike-fontes.md), implementá-lo agora
produziria um resíduo calculado sobre um terço do gasto real — enganoso, não
apenas incompleto.

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


def _termos_categoria(catmat: pd.DataFrame, categoria: str) -> list[str]:
    linha = catmat[catmat["categoria"] == categoria]
    if linha.empty:
        return []
    bruto = _normaliza(linha.iloc[0].get("palavras_chave", ""))
    return [t.strip() for t in bruto.split("|") if t.strip()]


def _municipio_comprou_categoria(
    compras: pd.DataFrame, cod_ibge: str, ano: int, categoria: str, catmat: pd.DataFrame
) -> bool:
    """Casamento por palavra-chave (coluna `palavras_chave` de
    `seeds/catmat_saude.csv`) entre o `objeto_compra` e a categoria de insumo —
    heurística simples e explicável, não NLP."""
    termos = _termos_categoria(catmat, categoria)
    if not termos or "objeto_compra" not in compras.columns:
        return False

    do_municipio = compras[(compras["cod_ibge"] == cod_ibge) & (compras["ano"] == ano)]
    if do_municipio.empty:
        return False

    objetos = do_municipio["objeto_compra"].fillna("").map(_normaliza)
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

    # Só é possível afirmar "não contratou o insumo" para um município-ano que
    # APARECE no PNCP naquele ano — se não há nenhuma compra publicada, o que
    # existe é ausência de dado, não ausência de política. Sem esse filtro o
    # detector confunde lacuna de cobertura do PNCP (a maioria dos casos hoje,
    # já que o portal só começa a ser universal com a Lei 14.133) com falha
    # real de resposta, e o alerta perde valor para auditoria.
    municipio_ano_com_compra = set(
        map(tuple, compras[["cod_ibge", "ano"]].dropna().drop_duplicates().to_numpy())
    )

    achados = []
    for agravo_cod, spec in agravo_insumo.items():
        col_taxa = f"taxa_{agravo_cod.lower()}"
        if col_taxa not in epidemiologia.columns:
            continue

        corte = epidemiologia[col_taxa].quantile(limiar)
        surto = epidemiologia[epidemiologia[col_taxa] >= corte]

        for _, row in surto.iterrows():
            if (row["cod_ibge"], row["ano"]) not in municipio_ano_com_compra:
                continue

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


def _normaliza(texto: str) -> str:
    import unicodedata

    s = unicodedata.normalize("NFKD", str(texto).lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def _categoria_do_item(descricao: str, catmat: pd.DataFrame) -> str | None:
    """Classifica o item numa categoria de `seeds/catmat_saude.csv` pela coluna
    `palavras_chave` (termos curados, separados por `|`), sem acento e como
    substring. Curado de propósito: o campo `descricao` é uma frase humana e
    casá-lo por palavra solta ("classe", "material") pega qualquer coisa."""
    texto = _normaliza(descricao)
    for _, linha in catmat.iterrows():
        termos = [
            t.strip() for t in _normaliza(linha.get("palavras_chave", "")).split("|") if t.strip()
        ]
        if any(t in texto for t in termos):
            return linha["categoria"]
    return None


def detectar_sobrepreco(itens: pd.DataFrame | None) -> pd.DataFrame:
    """Detector 3: preço unitário fora da curva dentro da mesma categoria de insumo.

    `itens` é o `silver/pncp_itens.parquet` (um registro por item de compra,
    com `valor_unitario_estimado`). Para cada categoria de insumo de saúde, o
    detector calcula o IQR dos preços unitários entre municípios e sinaliza os
    itens acima de Q3 + fator·IQR (fator em `conf/ieas.yml::alertas.preco_iqr_fator`).
    Comparar só dentro da categoria evita o falso-positivo óbvio de comparar o
    preço de uma seringa com o de um tomógrafo.
    """
    schema_vazio = pd.DataFrame(
        columns=["cod_ibge", "ano", "tipo", "severidade", "categoria", "explicacao"]
    )
    if itens is None or itens.empty:
        return schema_vazio

    fator = ieas_conf()["alertas"]["preco_iqr_fator"]
    catmat = _carregar_catmat()

    df = itens.copy()
    df = df[pd.to_numeric(df["valor_unitario_estimado"], errors="coerce") > 0]
    df["valor_unitario_estimado"] = df["valor_unitario_estimado"].astype(float)
    # itens com orçamento sigiloso não têm preço público confiável para comparar
    df = df[df["orcamento_sigiloso"] != True]
    # só MATERIAL: serviço/obra tem "preço unitário" de valor global (quantidade
    # 1), que não é comparável entre municípios.
    df = df[df["material_ou_servico"].astype(str).str.lower().str.startswith("mat")]
    df["categoria"] = df["descricao"].map(lambda d: _categoria_do_item(d, catmat))
    df = df.dropna(subset=["categoria"])
    # a categoria de obras de saneamento é, por definição, de valor global
    df = df[df["categoria"] != "material_obra_saneamento"]

    achados = []
    for categoria, grupo in df.groupby("categoria"):
        precos = grupo["valor_unitario_estimado"]
        if len(precos) < 5:  # sem base para uma distribuição
            continue
        q1, q3 = precos.quantile(0.25), precos.quantile(0.75)
        iqr = q3 - q1
        if iqr <= 0:
            continue
        limite = q3 + fator * iqr
        mediana = precos.median()
        for _, item in grupo[grupo["valor_unitario_estimado"] > limite].iterrows():
            razao = item["valor_unitario_estimado"] / mediana if mediana else float("inf")
            achados.append(
                {
                    "cod_ibge": item["cod_ibge"],
                    "ano": item["ano"],
                    "tipo": "suspeita_sobrepreco",
                    "severidade": "alta" if razao >= 3 else "moderada",
                    "categoria": categoria,
                    "explicacao": (
                        f"Item '{str(item['descricao'])[:60]}' contratado a "
                        f"R$ {item['valor_unitario_estimado']:,.2f}/{item['unidade_medida']} "
                        f"— {razao:.1f}× a mediana de PE para {categoria} "
                        f"(R$ {mediana:,.2f}). Contratação {item['numero_controle_pncp']}."
                    ).replace(",", "."),
                }
            )

    return pd.DataFrame(achados) if achados else schema_vazio


def rodar(
    df_ieas: pd.DataFrame,
    epidemiologia: pd.DataFrame,
    compras: pd.DataFrame | None,
    itens: pd.DataFrame | None = None,
):
    d1 = detectar_desalinhamento_estrutural(df_ieas)
    d4 = detectar_desabastecimento(epidemiologia, compras)
    d3 = detectar_sobrepreco(itens)
    comuns = ["cod_ibge", "ano", "tipo", "severidade", "explicacao"]
    return pd.concat([d1[comuns], d4[comuns], d3[comuns]], ignore_index=True)

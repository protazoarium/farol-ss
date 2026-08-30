"""Detectores de gargalo e vulnerabilidade — os quatro do plano.

1. Desalinhamento estrutural — o farol vermelho: corte fixo no `gap`.
2. Alocação abaixo do esperado — resíduo de um ajuste robusto
   necessidade→alocação, por ano. Controla pela relação do estado inteiro, ao
   contrário do detector 1. Só roda onde o eixo de Alocação está completo
   (L1+L2+L3).
3. Suspeita de sobrepreço — preço unitário de um item acima de Q3 + fator·IQR
   da mesma categoria, unidade de medida E dose/concentração em PE. Usa
   `silver/pncp_itens.parquet`
   (ver `ingest/pncp_itens.py`), que puxa o preço por item do recurso
   `/v1/orgaos/{cnpj}/compras/{ano}/{seq}/itens` do PNCP — o recurso de consulta
   genérico só traz o valor total da compra.
4. Suspeita de desabastecimento — o detector mais original: liga incidência
   sustentada de um agravo (SINAN) à ausência de contratação da categoria de
   insumo correspondente (PNCP), via `seeds/agravo_insumo.yml`.

Cada detector devolve linhas com `explicacao` em texto legível — um alerta
sem explicação não serve para auditoria cidadã.
"""

from __future__ import annotations

import re

import numpy as np
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


def _corpus_compras_por_municipio_ano(
    compras: pd.DataFrame, itens: pd.DataFrame | None
) -> dict[tuple[str, int], str]:
    """Junta, por (cod_ibge, ano), todo o texto que descreve o que o município
    comprou: o `objeto_compra` da contratação (genérico, nível de processo) E a
    `descricao` de cada item (específica — "AMOXICILINA 500MG", "larvicida...").

    Consultar o item, não só o objeto, é o que torna o detector 4 capaz de
    afirmar "não comprou o insumo" com alguma precisão: um objeto "aquisição de
    medicamentos" não diz nada, mas os itens dizem.
    """
    corpus: dict[tuple[str, int], list[str]] = {}
    if "objeto_compra" in compras.columns:
        for cod, ano, obj in zip(
            compras["cod_ibge"], compras["ano"], compras["objeto_compra"].fillna("")
        ):
            corpus.setdefault((cod, int(ano)), []).append(_normaliza(obj))
    if itens is not None and not itens.empty and "descricao" in itens.columns:
        for cod, ano, desc in zip(itens["cod_ibge"], itens["ano"], itens["descricao"].fillna("")):
            corpus.setdefault((cod, int(ano)), []).append(_normaliza(desc))
    return {k: " || ".join(v) for k, v in corpus.items()}


def _comprou_categoria(texto: str, categoria: str, catmat: pd.DataFrame) -> bool:
    """`texto` é o corpus de compras de um município-ano (ver acima). Casamento
    por palavra-chave curada (`seeds/catmat_saude.csv`) — heurística explicável,
    não NLP nem classificação CATMAT estruturada (o PNCP não expõe a categoria
    CATMAT do item: `itemCategoriaNome` vem "Não se aplica" em 100% dos casos)."""
    termos = _termos_categoria(catmat, categoria)
    return bool(termos) and any(t in texto for t in termos)


def detectar_desabastecimento(
    epidemiologia: pd.DataFrame,
    compras: pd.DataFrame | None,
    itens: pd.DataFrame | None = None,
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
    corpus = _corpus_compras_por_municipio_ano(compras, itens)
    municipio_ano_com_compra = set(corpus)

    achados = []
    for agravo_cod, spec in agravo_insumo.items():
        col_taxa = f"taxa_{agravo_cod.lower()}"
        if col_taxa not in epidemiologia.columns:
            continue

        corte = epidemiologia[col_taxa].quantile(limiar)
        surto = epidemiologia[epidemiologia[col_taxa] >= corte]

        for _, row in surto.iterrows():
            chave = (row["cod_ibge"], int(row["ano"]))
            if chave not in municipio_ano_com_compra:
                continue

            texto = corpus[chave]
            comprou_algo = any(
                _comprou_categoria(texto, cat, catmat) for cat in spec["insumos_esperados"]
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
                            "encontrada no PNCP (objeto e itens) para o município "
                            "no período."
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


# normalização de unidade de medida do PNCP (só o suficiente para agrupar
# preços comparáveis; um "frasco" e uma "ampola" do mesmo antibiótico não
# devem entrar na mesma distribuição).
_UNIDADES = {
    "un": "unidade",
    "und": "unidade",
    "unid": "unidade",
    "unidade": "unidade",
    "ud": "unidade",
    "cx": "caixa",
    "caixa": "caixa",
    "cxa": "caixa",
    "fr": "frasco",
    "frasco": "frasco",
    "fco": "frasco",
    "frs": "frasco",
    "frasco/ampola": "frasco",
    "amp": "ampola",
    "ampola": "ampola",
    "ampolas": "ampola",
    "cp": "comprimido",
    "comp": "comprimido",
    "comprimido": "comprimido",
    "cpr": "comprimido",
    "compr": "comprimido",
    "cápsula": "comprimido",
    "capsula": "comprimido",
    "ml": "ml",
    "l": "litro",
    "litro": "litro",
    "kg": "kg",
    "g": "grama",
    "grama": "grama",
    "tubo": "tubo",
    "bisnaga": "tubo",
    "envelope": "envelope",
    "sache": "envelope",
    "sachê": "envelope",
    "teste": "teste",
    "kit": "kit",
    "unitário": "unidade",
}


def _unidade_norm(u) -> str:
    return _UNIDADES.get(_normaliza(u).strip(), _normaliza(u).strip() or "sem_unidade")


# dose/concentração declarada na descrição do item ("AMOXICILINA 500MG",
# "50mg/ml", "0,9%"). Ordem importa: os compostos (mg/ml) antes dos simples.
_DOSE_RE = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(mg/ml|mcg/ml|ui/ml|mg/g|mg|mcg|ui|g|ml|%)", re.IGNORECASE
)


def _dose_norm(descricao) -> str:
    """Assinatura da dose de um item, para não comparar preços de
    apresentações diferentes ("comprimido 500 mg" vs "250 mg"). Devolve string
    vazia quando não há dose parseável — nesse caso o item é comparado só por
    (categoria, unidade), como antes.

    Um conjunto ordenado captura combinações ("amoxicilina 500mg + clavulanato
    125mg" → "125mg+500mg"), que são um produto distinto do simples 500mg.
    """
    txt = _normaliza(descricao)
    achados = set()
    for val, uni in _DOSE_RE.findall(txt):
        try:
            f = float(val.replace(",", "."))
        except ValueError:
            continue
        achados.add(f"{f:g}{uni.lower()}")
    return "+".join(sorted(achados))


def _achados_grupo(grupo: pd.DataFrame, rotulo: str, fator: float) -> list[dict]:
    """Sinaliza itens acima de Q3 + fator·IQR dentro de `grupo` (já homogêneo
    em categoria/unidade/dose). `rotulo` descreve o grupo para a explicação."""
    precos = grupo["valor_unitario_estimado"]
    if len(precos) < 5:  # sem base para uma distribuição
        return []
    q1, q3 = precos.quantile(0.25), precos.quantile(0.75)
    iqr = q3 - q1
    if iqr <= 0:
        return []
    limite = q3 + fator * iqr
    mediana = precos.median()
    out = []
    for _, item in grupo[grupo["valor_unitario_estimado"] > limite].iterrows():
        razao = item["valor_unitario_estimado"] / mediana if mediana else float("inf")
        out.append(
            {
                "cod_ibge": item["cod_ibge"],
                "ano": item["ano"],
                "tipo": "suspeita_sobrepreco",
                "severidade": "alta" if razao >= 3 else "moderada",
                "categoria": item["categoria"],
                "explicacao": (
                    f"Item '{str(item['descricao'])[:60]}' contratado a "
                    f"R$ {item['valor_unitario_estimado']:,.2f} — {razao:.1f}× a "
                    f"mediana de PE para {rotulo} (R$ {mediana:,.2f}). "
                    f"Contratação {item['numero_controle_pncp']}."
                ).replace(",", "."),
            }
        )
    return out


def detectar_sobrepreco(itens: pd.DataFrame | None) -> pd.DataFrame:
    """Detector 3: preço unitário fora da curva dentro da mesma categoria de
    insumo, **da mesma unidade de medida e da mesma dose/concentração**.

    `itens` é o `silver/pncp_itens.parquet` (um registro por item de compra,
    com `valor_unitario_estimado`). O detector calcula o IQR dos preços
    unitários entre municípios e sinaliza os itens acima de Q3 + fator·IQR
    (`conf/ieas.yml::alertas.preco_iqr_fator`).

    Duas camadas de agrupamento:

    1. **fina** — (categoria, unidade, dose): compara "amoxicilina cápsula
       500 mg" só com outras "amoxicilina cápsula 500 mg", nunca com a de
       250 mg nem com a suspensão 50 mg/ml. Só vale quando o grupo tem ≥ 5
       itens com dose parseável.
    2. **grossa** — (categoria, unidade): recebe os itens sem dose parseável
       ou cujo grupo fino é pequeno demais. É o comportamento anterior.
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
    df["unidade_norm"] = df["unidade_medida"].map(_unidade_norm)
    df["dose_norm"] = df["descricao"].map(_dose_norm)

    achados: list[dict] = []
    coberto = pd.Series(False, index=df.index)

    # 1. camada fina: (categoria, unidade, dose) com dose e ≥ 5 itens
    com_dose = df[df["dose_norm"] != ""]
    for (cat, uni, dose), grupo in com_dose.groupby(["categoria", "unidade_norm", "dose_norm"]):
        if len(grupo) < 5:
            continue
        coberto.loc[grupo.index] = True
        achados += _achados_grupo(grupo, f"{cat} {dose} ({uni})", fator)

    # 2. camada grossa: (categoria, unidade) para o que sobrou
    resto = df[~coberto]
    for (cat, uni), grupo in resto.groupby(["categoria", "unidade_norm"]):
        achados += _achados_grupo(grupo, f"{cat} ({uni}, dose não normalizada)", fator)

    return pd.DataFrame(achados) if achados else schema_vazio


def detectar_residuo_alocacao(df_ieas: pd.DataFrame) -> pd.DataFrame:
    """Detector 2: alocação muito abaixo do que a necessidade prevê.

    Ao contrário do detector 1 (que é o farol vermelho, um corte fixo no
    `gap`), este controla pela **relação necessidade→alocação do estado**:
    ajusta, por ano, uma reta `alocacao_rank ~ necessidade_rank` e mede o
    resíduo de cada município. A escala do resíduo é robusta (1,4826·MAD), não
    o desvio-padrão, para que os próprios *outliers* não inflem o corte.
    Sinaliza quem tem resíduo padronizado ≤ −`alertas.residuo_z_minimo`
    (`conf/ieas.yml`) — alocação sistematicamente aquém, dado o padrão do
    estado.

    Só roda sobre município-anos com o eixo de Alocação inteiro (L1+L2+L3);
    onde falta camada, o rank de alocação é NaN e a linha fica de fora.
    """
    schema_vazio = pd.DataFrame(
        columns=["cod_ibge", "ano", "tipo", "severidade", "residuo_z", "explicacao"]
    )
    cols = {"necessidade_rank", "alocacao_rank", "alocacao_cobertura"}
    if not cols.issubset(df_ieas.columns):
        return schema_vazio

    z_min = ieas_conf()["alertas"]["residuo_z_minimo"]
    base = df_ieas[
        df_ieas["necessidade_rank"].notna()
        & df_ieas["alocacao_rank"].notna()
        & (df_ieas["alocacao_cobertura"] >= 0.99)  # eixo A completo
    ].copy()

    achados = []
    for ano, grupo in base.groupby("ano"):
        if len(grupo) < 15:  # amostra pequena demais para um ajuste
            continue
        x = grupo["necessidade_rank"].to_numpy()
        y = grupo["alocacao_rank"].to_numpy()
        coef = np.polyfit(x, y, 1)
        residuo = y - np.polyval(coef, x)
        escala = 1.4826 * np.median(np.abs(residuo - np.median(residuo)))
        if escala <= 0:
            continue
        z = (residuo - np.median(residuo)) / escala
        for (_, linha), zi, ri in zip(grupo.iterrows(), z, residuo):
            # exige desvio estatístico E prático (≥ 8 pontos percentuais abaixo
            # do previsto) — assim ruído gaussiano normal não vira alerta.
            if zi <= -z_min and ri <= -0.08:
                achados.append(
                    {
                        "cod_ibge": linha["cod_ibge"],
                        "ano": int(ano),
                        "tipo": "alocacao_abaixo_do_esperado",
                        "severidade": "alta" if zi <= -3 else "moderada",
                        "residuo_z": round(float(zi), 2),
                        "explicacao": (
                            f"Alocação no percentil {linha['alocacao_rank']:.0%}, "
                            f"mas o padrão necessidade→alocação de PE em {int(ano)} "
                            f"previa ~{np.polyval(coef, linha['necessidade_rank']):.0%} "
                            f"para uma necessidade no percentil "
                            f"{linha['necessidade_rank']:.0%} — resíduo de {zi:.1f} "
                            "desvios robustos abaixo do esperado."
                        ),
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
    d2 = detectar_residuo_alocacao(df_ieas)
    d3 = detectar_sobrepreco(itens)
    d4 = detectar_desabastecimento(epidemiologia, compras, itens)
    comuns = ["cod_ibge", "ano", "tipo", "severidade", "explicacao"]
    return pd.concat([d1[comuns], d2[comuns], d3[comuns], d4[comuns]], ignore_index=True)

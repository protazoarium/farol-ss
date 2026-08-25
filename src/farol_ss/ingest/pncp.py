"""Ingestão de contratações municipais via PNCP.

O PNCP é a plataforma onde as prefeituras publicam licitações sob a Lei
14.133 — é a fonte que de fato viabiliza a camada L3 (contratação de
insumos) por município, ao contrário do Compras.gov.br, que é escopo
federal (UASGs). A validação do endpoint real está registrada em
`docs/spike-fontes.md`; aqui documentamos o que essa validação exigiu.

O endpoint certo é `/v1/contratacoes/publicacao` (não `/v1/contratos`, que
só filtra por CNPJ de órgão federal já conhecido — inútil sem uma lista de
CNPJs municipais). `/v1/contratacoes/publicacao` aceita `uf` diretamente,
então consultamos PE inteiro por modalidade/ano e extraímos o município de
`unidadeOrgao.codigoIbge` no retorno — em vez de 185 × 5 chamadas (uma por
município), são ~14 modalidades × 5 anos, muito mais barato.

`codigoModalidadeContratacao` é obrigatório e não vem como enum no OpenAPI;
os códigos abaixo são a tabela de domínio publicada no manual do PNCP.
"""

from __future__ import annotations

import pandas as pd

from farol_ss import config
from farol_ss.ingest.base import Fetcher, Proveniencia, _agora, registrar, sha256
from farol_ss.io import duck
from farol_ss.io import municipios as M

# Tabela de domínio completa do PNCP (manual de integração), para referência.
MODALIDADES_TODAS = {
    1: "Leilão - Eletrônico",
    2: "Diálogo Competitivo",
    3: "Concurso",
    4: "Concorrência - Eletrônica",
    5: "Concorrência - Presencial",
    6: "Pregão - Eletrônico",
    7: "Pregão - Presencial",
    8: "Dispensa de Licitação",
    9: "Inexigibilidade",
    10: "Manifestação de Interesse",
    11: "Pré-qualificação",
    12: "Credenciamento",
    13: "Leilão - Presencial",
    14: "Inaplicabilidade da Licitação",
}

# Escopo da ingestão: só as modalidades que de fato compram insumos de saúde
# e obras de saneamento. Medido empiricamente: só "Dispensa de Licitação"
# 2024 tem 310 páginas (~10 min a 2s/página); as 14 modalidades completas
# multiplicariam isso por quase 3x sem ganho para o IEAS. Concorrência
# (obras de saneamento), Pregão (compras de bens/insumos, inclusive
# medicamentos) e Inexigibilidade (compras emergenciais, comum em saúde)
# cobrem o que interessa. Leilão, Concurso, Credenciamento etc. ficam de
# fora — não são o tipo de contratação que move a camada L3 do IEAS.
MODALIDADES = {k: v for k, v in MODALIDADES_TODAS.items() if k in {4, 6, 7, 8, 9}}

COLUNAS_UTEIS = [
    "cod_ibge",
    "ano",
    "modalidade_id",
    "modalidade_nome",
    "numero_controle_pncp",
    "objeto_compra",
    "valor_total_homologado",
    "valor_total_estimado",
    "data_publicacao_pncp",
    "situacao_compra_nome",
]


def _extrair_linha(item: dict, ano: int) -> dict | None:
    uo = item.get("unidadeOrgao") or {}
    cod = uo.get("codigoIbge")
    if not cod or cod not in M.codigos():
        return None
    return {
        "cod_ibge": cod,
        "ano": ano,
        "modalidade_id": item.get("modalidadeId"),
        "modalidade_nome": item.get("modalidadeNome"),
        "numero_controle_pncp": item.get("numeroControlePNCP"),
        "objeto_compra": item.get("objetoCompra"),
        "valor_total_homologado": item.get("valorTotalHomologado"),
        "valor_total_estimado": item.get("valorTotalEstimado"),
        "data_publicacao_pncp": item.get("dataPublicacaoPncp"),
        "situacao_compra_nome": item.get("situacaoCompraNome"),
    }


def ingerir_modalidade_ano(f: Fetcher, modalidade_id: int, ano: int) -> pd.DataFrame | None:
    """Pagina uma modalidade/ano para PE inteiro (tamanhoPagina máximo é 50).

    O PNCP é comprovadamente instável: testes manuais durante o
    desenvolvimento pegaram timeout total (sem resposta), HTTP 204 sem corpo
    e 200 normal para a MESMA consulta em tentativas sucessivas — e uma
    execução real ficou 11 minutos travada sem produzir nenhum arquivo antes
    de precisar ser interrompida manualmente (ver docs/spike-fontes.md). Por
    isso cada página é isolada num try/except próprio: se uma página falhar
    mesmo após o retry do Fetcher, a paginação PARA e devolve o que já foi
    coletado até ali, em vez de perder o bloco inteiro de modalidade/ano ou
    travar o processo inteiro esperando uma página que talvez nunca responda.
    """
    url = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"
    linhas = []
    pagina = 1
    while True:
        try:
            r = f.get(
                url,
                dataInicial=f"{ano}0101",
                dataFinal=f"{ano}1231",
                codigoModalidadeContratacao=modalidade_id,
                uf="PE",
                pagina=pagina,
                tamanhoPagina=50,
            )
        except Exception as e:
            print(
                f"    ⚠ PNCP modalidade {modalidade_id} {ano} pág {pagina}: "
                f"{type(e).__name__} — parando com {len(linhas)} linhas coletadas até aqui"
            )
            break

        if r.status_code in (422, 404):
            break
        if r.status_code == 204 or not r.content:
            # Corpo vazio: nada mais nesta página, mas não é erro de fato
            break
        r.raise_for_status()
        body = r.json()
        for item in body.get("data", []):
            linha = _extrair_linha(item, ano)
            if linha:
                linhas.append(linha)
        if pagina >= body.get("totalPaginas", 0):
            break
        pagina += 1
        if pagina > 300:  # guarda contra loop infinito
            break

    if not linhas:
        return None
    return pd.DataFrame(linhas, columns=COLUNAS_UTEIS)


def ingerir_pncp() -> None:
    """Ingerir contratações municipais de PE para todas as modalidades e anos."""
    config.ensure_dirs()
    duck.exigir_espaco(minimo_gb=1.0)
    anos = config.anos()

    with Fetcher("pncp") as f:
        for modalidade_id, modalidade_nome in MODALIDADES.items():
            for ano in anos:
                try:
                    df = ingerir_modalidade_ano(f, modalidade_id, ano)
                except Exception as e:
                    print(
                        f"  ✗ PNCP modalidade {modalidade_id} {ano}: {type(e).__name__} {str(e)[:80]}"
                    )
                    continue

                if df is None or df.empty:
                    continue

                path = duck.write_silver(df, f"pncp_{modalidade_id}_{ano}")
                registrar(
                    Proveniencia(
                        fonte=f"pncp_{modalidade_id}_{ano}",
                        url="https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao",
                        coletado_em=_agora(),
                        arquivo=str(path.relative_to(config.ROOT)),
                        sha256=sha256(df.to_csv(index=False).encode()),
                        bytes=df.memory_usage(deep=True).sum().item(),
                        linhas=len(df),
                        extra={"modalidade": modalidade_nome, "ano": ano},
                    )
                )
                print(
                    f"  ✓ {modalidade_nome} {ano}: {len(df)} compras, "
                    f"{df['cod_ibge'].nunique()} municípios"
                )


def rodar() -> None:
    """Ingerir PNCP para PE."""
    ingerir_pncp()

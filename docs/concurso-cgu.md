# 2º Concurso de Reúso de Dados Abertos da CGU — regras e checklist

Fonte: <https://www.gov.br/cgu/pt-br/acesso-a-informacao/dados-abertos/concurso-dados-abertos/concurso-de-reuso-de-dados-abertos-da-cgu>
Edital publicado no DOU em 23/06/2026. Consulta feita em 29/08/2026.

## Prazos

| Data | Evento |
|---|---|
| 29/06/2026 | Abertura das inscrições |
| **11/09/2026** | **Encerramento das inscrições** |
| 25/09/2026 | Resultado preliminar de admissibilidade |
| 28/09–02/10/2026 | Recursos |
| 12/10/2026 | Resultado final de admissão |
| 13/11/2026 | Resultado preliminar do julgamento |
| 16–20/11/2026 | Recursos |
| 09/12/2026 | Resultado final |
| até 30/03/2027 | Entrega das premiações |

## Quem pode participar

Qualquer pessoa — cidadãos, servidores/empregados públicos, setor privado,
academia, sociedade civil, imprensa, organismos internacionais. Individual ou
em grupo de **até 20 pessoas**. Várias iniciativas por pessoa/grupo são
permitidas; cada submissão conta como uma iniciativa. O edital não lista
vedação a servidores da CGU ou a membros de comissão no conteúdo público da
página — confirmar no PDF do edital antes de assumir.

## Como inscrever — duas etapas obrigatórias

1. **Formulário da CGU** — <https://formularios.cgu.gov.br/index.php/263319>
   Informações gerais da iniciativa + dados dos desenvolvedores (até 20).
   Opcional: anexar imagens, logo, apresentação.
2. **Publicar o reúso no dados.gov.br** — cadastro como usuário consumidor ou
   organização, submeter a iniciativa informando **a(s) URL(s) do(s) conjunto(s)
   de dados usados** e selecionar **"Enviar para homologação"**.
   Guia: "Saiba como publicar um reúso" no Portal Dados.Gov.

## Requisito duro sobre as fontes

Pelo menos **um** dos conjuntos de dados usados precisa estar catalogado no
Portal Brasileiro de Dados Abertos (dados.gov.br). **Não** precisa ser dado da
CGU — qualquer organização serve. O Farol-SS cumpre com folga: IBGE
(população, IPCA, malhas), SINAN, SIH, PNCP, SIOPS, CadÚnico, Compras.gov.br e
o próprio Portal da Transparência da CGU têm entrada no dados.gov.br (URLs em
`conf/sources.yml`, campo `dados_gov`).

## Critérios de julgamento (total 11 pontos)

| Critério | Peso | Onde o Farol-SS pontua | Lacuna |
|---|---|---|---|
| Apresentação | 2 | painel Streamlit, README, docs de metodologia; o farol tem cor (921/925 município-anos, 185/185 em 2024) | falta demo hospedada ou vídeo |
| Inovação | 2 | detector de desabastecimento (incidência SINAN sustentada × ausência de compra do insumo no PNCP) | descrever bem esse diferencial no formulário |
| Transparência / fomento ao controle social | 2 | proveniência (`manifest.json`), alertas com `explicacao` legível, enfoque "auditoria cidadã" | página de Metodologia expondo isso ao público |
| Foco nas pessoas / impacto social | 2 | desfecho é carga de doença evitável por município | enquadrar a narrativa em saúde, não em dado |
| Múltiplas fontes de dados | 1 | cruza IBGE + SINAN + SIH + PNCP + Compras.gov.br + SIOPS + CadÚnico + Censo 2022 | ponto garantido |
| Uso de ferramentas tecnológicas | 1 | pipeline em camadas, DuckDB sobre Parquet, Streamlit | ok |
| Inclusão / acessibilidade | 1 | paleta do semáforo validada para daltonismo (dataviz skill) | declarar explicitamente: tabela alternativa a cada mapa, contraste, textos alt |

## Formato do entregável

Aceitos: apps, modelos de IA, novos negócios, produtos, **painéis**,
**plataformas**, reportagens, ações sociais, ferramentas. O painel Streamlit
se encaixa direto na categoria "painel". Não há exigência explícita de código
aberto, repositório público ou licença específica — mas repositório público
reforça Apresentação e Transparência, e a Etapa 2 é uma publicação pública de
reúso, então é preciso ter uma URL acessível (demo hospedada) ou, no mínimo,
um vídeo mostrando o painel funcionando.

## Premiação

Três primeiras iniciativas: reconhecimento formal da CGU, certificado, direito
de uso do selo "Dados Abertos" em material de divulgação, e inclusão no banco
de soluções inovadoras do dados.gov.br. (Não é prêmio em dinheiro.)

## Checklist até 11/09/2026

- [ ] Preencher a Etapa 1 (formulário CGU) — não esperar o código ficar pronto; pode revisar depois
- [ ] Publicar o reúso no dados.gov.br com as URLs de `conf/sources.yml` e "Enviar para homologação"
- [ ] Ler o PDF do edital (DOU 23/06/2026) e conferir: vedações, exigência de anexos, formato de vídeo
- [x] Preparar arquivos de deploy do painel (`requirements.txt`, `.gitignore`, `docs/deploy.md`) — **falta o push + "New app" no Streamlit Cloud**
- [ ] Hospedar a demo (seguir `docs/deploy.md`) **ou** gravar um screencast de 2–3 min
- [ ] Página de Metodologia pública (fórmula do IEAS, tabela de proveniência)
- [ ] Declaração de acessibilidade (tabela alternativa a cada mapa, paleta CVD, contraste)
- [x] Destravar as fontes de Alocação — feito: SIOPS (L2), PNCP + Compras.gov.br (L3), L1 completo (Transparência, 185/185). O farol tem cor.

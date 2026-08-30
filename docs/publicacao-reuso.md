# Publicação do reúso — valores para os formulários

Guia de preenchimento dos dois formulários exigidos para submeter o Farol-SS ao
**2º Concurso de Reúso de Dados Abertos da CGU** (cronograma e regras em
`docs/concurso-cgu.md`; passo a passo de navegação em
`docs/passo-a-passo-dados-gov.md`).

> **Ordem correta**: primeiro faça o **deploy do painel** (`docs/deploy.md`, que
> agora traz o passo a passo do login no Streamlit Cloud) para ter uma URL
> pública; só então preencha os formulários, que pedem essa URL.
>
> **Estado do projeto (v1.4)**: pipeline completo, oito fontes, **L1 completo**
> (185/185 × 5 anos), IEAS calculado para 921 dos 925 município-anos, 777
> alertas explicáveis. Painel com sistema de design institucional, diagrama do
> índice e página de Metodologia com todas as fórmulas. Falta só o deploy.

---

## Pré-requisitos

| Item | Situação |
|---|---|
| Conta **gov.br** (a mesma serve para o dados.gov.br e para o formulário da CGU) | do autor |
| **Perfil de consumidor** no Portal de Dados Abertos (usuário comum) | criar no primeiro acesso — ver passo a passo |
| Repositório público | ✅ <https://github.com/protazoarium/farol-ss> (branch `main` atualizada, v1.4) |
| Painel no ar (Streamlit Community Cloud) | ⏳ pendente — passos em `docs/deploy.md` (inclui como logar e deixar o app público). **URL de publicação:** `https://farol-ss.streamlit.app` (reservar esse subdomínio no deploy) |
| Logo 1:1 ≥ 200×200 px | criar (sugestão: o emoji 🚦 sobre fundo `#1257a8`, ou um recorte do mapa) |
| 1–3 telas do painel 1:1 ≥ 200×200 px | recortar do painel: mapa da página **Farol**, o **diagrama do índice** na Home ou na Metodologia, e a página **Alertas** ou **Fontes** |

---

## Etapa 1 — Formulário da CGU

**Onde**: <https://formularios.cgu.gov.br/index.php/263319>

| Campo | O que informar |
|---|---|
| Nome da iniciativa | **Farol da Saúde & Saneamento (Farol-SS)** |
| Descrição curta | Monitor territorial que cruza execução financeira em saúde com carga epidemiológica, déficit de saneamento e vulnerabilidade social, produzindo o IEAS — Índice de Efetividade da Alocação Sanitária — para os 185 municípios de Pernambuco. |
| Tipo de solução | Painel / plataforma de dados |
| URL da solução | `https://farol-ss.streamlit.app` |
| Repositório | <https://github.com/protazoarium/farol-ss> |
| Conjuntos de dados usados (dados.gov.br) | ver lista na seção "Conjunto de dados de origem" abaixo |
| Desenvolvedores | *(nome, e-mail — até 20 pessoas)* |
| Anexos (opcional) | logo, 2–3 capturas de tela do painel, este relatório em PDF/DOCX |

Depois de enviar, **avance imediatamente para a Etapa 2**.

---

## Etapa 2 — Cadastro do reúso no dados.gov.br

**Onde**: dashboard do dados.gov.br → menu lateral esquerdo **"Reúsos"** →
**"Adicionar reúso"**. Dicionário oficial dos campos abaixo, já preenchido.

| Campo do formulário | Valor a digitar |
|---|---|
| **Nome** | `Farol da Saúde & Saneamento (Farol-SS)` |
| **URL** | `https://farol-ss.streamlit.app` |
| **Descrição** *(máx. 255 caracteres)* | `IEAS — Índice de Efetividade da Alocação Sanitária para os 185 municípios de Pernambuco: cruza gasto público em saúde (SIOPS, PNCP, Transparência) com carga de doença (SINAN, SIH), saneamento (Censo 2022) e vulnerabilidade (CadÚnico). Painel e API.` *(248 caracteres)* |
| **Tipos** | `Painel` |
| **Nome do responsável** | *(nome do autor)* |
| **Email do responsável** | *(e-mail do autor)* |
| **Data de lançamento do reúso** | *(a data em que o `farol-ss.streamlit.app` ficou público — ver `docs/deploy.md` passo 4)* |
| **Botão de descontinuado** | deixar em branco (o reúso está ativo) |
| **Logo do reúso** | imagem 1:1 ≥ 200×200 px (ver pré-requisitos) |
| **Telas do reúso** | 1–3 capturas do painel, 1:1 ≥ 200×200 px |
| **Organização/Autor** | preenchido automaticamente (não editável) — sairá como o consumidor |
| **Conjunto de dados de origem** | selecionar os conjuntos da tabela abaixo (busca por nome dentro do próprio campo) |
| **Conjunto de dados não catalogados** | ver seção "Conjuntos não catalogados" |
| **Temas** | `Saúde` (principal); adicionar `Economia e Finanças` e `Governo e Política` |
| **Palavras-chave** | `IEAS; saúde pública; dados abertos; contratações públicas; PNCP; SINAN; SIH; SIOPS; CadÚnico; saneamento; Censo 2022; Pernambuco; controle social; arboviroses; vulnerabilidade social` |
| **Visibilidade** | **Pública** |

Depois: **Salvar** → abrir de novo em **Editar** → rolar até o fim →
**"Enviar para homologação"**. O reúso fica como *pendente de homologação*
aguardando a autorização da CGU.

> ⚠️ Se você **editar** o reúso depois de enviá-lo, o status volta para
> "Em edição" e é preciso reenviar para homologação. Deixe para editar só se
> for realmente necessário.

---

## Conjunto de dados de origem (catalogados no dados.gov.br)

O concurso exige **pelo menos um**. O Farol-SS referencia **treze conjuntos
catalogados** no dados.gov.br — selecione todos no campo "Conjunto de dados de
origem" (o campo tem busca por nome):

| Conjunto (nome no portal) | URL | Uso no Farol-SS |
|---|---|---|
| Sinan/Dengue | `dados.gov.br/dados/conjuntos-dados/arboviroses-dengue` | subíndice epidemiológico (arboviroses) |
| Sinan/Febre de Chikungunya | `dados.gov.br/dados/conjuntos-dados/arboviroses-febre-de-chikungunya` | subíndice epidemiológico (arboviroses) |
| Sinan/Vírus Zika | `dados.gov.br/dados/conjuntos-dados/arboviroses-zika-virus` | subíndice epidemiológico (arboviroses) |
| Sistema de Informações Hospitalares do SUS — SIH/SUS | `dados.gov.br/dados/conjuntos-dados/sistema-de-informacoes-hospitalares-do-sus-sihsus` | subíndice epidemiológico — internações por doença relacionada a saneamento (DRSAI) |
| Censo Demográfico 2022 | `dados.gov.br/dados/conjuntos-dados/censo-demografico-2022` | subíndice de saneamento (déficit de água/esgoto/lixo) |
| Famílias Inscritas no Cadastro Único | `dados.gov.br/dados/conjuntos-dados/familias-inscritas-no-cadastro-unico` | subíndice de vulnerabilidade (extrema pobreza) |
| Sistema de Informações sobre Orçamentos Públicos em Saúde — SIOPS | `dados.gov.br/dados/conjuntos-dados/siops` | eixo Alocação, camada L2 (execução própria municipal) |
| Portal Nacional de Contratações Públicas — PNCP | `dados.gov.br/dados/conjuntos-dados/pncp` | eixo Alocação, camada L3 (compras de insumos) + detector de sobrepreço |
| Compras Públicas do Governo Federal (Compras.gov.br) | `dados.gov.br/dados/conjuntos-dados/compras-publicas-do-governo-federal` | eixo Alocação, camada L3 federal (complemento) |
| Portal da Transparência do Governo Federal | `dados.gov.br/dados/conjuntos-dados/portal-da-transparencia-do-governo-federal` | eixo Alocação, camada L1 (repasse federal — proxy de transferências sociais) |
| Estimativas de População | `dados.gov.br/dados/conjuntos-dados/estimativas-de-populacao` | denominador de toda taxa por 100 mil habitantes |
| Índice Nacional de Preços ao Consumidor Amplo — IPCA | `dados.gov.br/dados/conjuntos-dados/indice-nacional-de-precos-ao-consumidor-amplo-ipca` | deflator (todos os valores em R$ de 2024) |
| Malha Geométrica dos Municípios Brasileiros | `dados.gov.br/dados/conjuntos-dados/malha-geometrica-dos-municipios-brasileiros` | geometria do mapa coroplético |

*(As três arboviroses do SINAN contam como três conjuntos distintos no portal.
Leptospirose, hepatite A e esquistossomose do SINAN também alimentam o índice,
mas não têm conjunto próprio catalogado — entram como não catalogados, abaixo.
URLs verificadas em 30/08/2026.)*

---

## Conjuntos de dados não catalogados

Campo "Conjunto de dados não catalizados" — separar por ponto-e-vírgula, URL
entre parênteses:

```
SINAN — Leptospirose, Hepatite A e Esquistossomose, obtidos via PySUS (não têm conjunto próprio no portal; só as arboviroses têm) (https://github.com/AlertaDengue/PySUS); CadÚnico — taxa de extrema pobreza pela Matriz de Informações Sociais da SAGI/MDS, endpoint misocial (o conjunto catalogado "Famílias Inscritas no CadÚnico" traz o extrato mensal, não esse agregado) (https://aplicacoes.mds.gov.br/sagi/servicos/misocial)
```

Os agregados do IBGE usados via API `servicodados` (população 6579, IPCA 1737,
Censo 2022 6803/6805/6892) **correspondem a conjuntos catalogados** — já estão
na tabela acima; não precisam entrar como não catalogados.

---

## Texto longo (caso o formulário peça uma descrição estendida)

> O **Farol da Saúde & Saneamento (Farol-SS)** é um monitor territorial que
> torna visível o descompasso entre o quanto um município **precisa** e o
> quanto ele **recebe e gasta** em saúde. Para os 185 municípios de Pernambuco
> (2020–2024), o projeto cruza **oito fontes federais abertas** — carga
> epidemiológica (SINAN e internações do SIH), déficit de saneamento (Censo
> 2022 do IBGE), vulnerabilidade social (CadÚnico), execução própria municipal
> em saúde (SIOPS), contratação de insumos (PNCP e Compras.gov.br) e repasse
> federal (Portal da Transparência) — num grão único de município × ano, e
> produz o **IEAS — Índice de Efetividade da Alocação Sanitária**: dois eixos
> normalizados por rank percentil dentro do estado, cuja diferença colore um
> semáforo (vermelho = necessidade não atendida).
>
> A entrega é um **pipeline de dados reprodutível** (do dado bruto ao índice,
> com proveniência rastreável em `manifest.json`), um **painel web** com mapa
> coroplético acessível (paleta validada para daltonismo), um **diagrama de
> construção do índice** e uma página de **Metodologia que expõe todas as
> fontes e todas as fórmulas** em notação matemática, e uma **API aberta** em
> JSON/CSV. Quatro detectores geram **alertas explicáveis em linguagem
> natural** para auditoria cidadã, incluindo a suspeita de desabastecimento
> (incidência sustentada de um agravo sem a contratação do insumo
> correspondente) e a suspeita de sobrepreço (preço unitário de insumo fora da
> curva da mesma categoria, unidade e dose no estado).
>
> Painel: <https://farol-ss.streamlit.app> · Código aberto sob domínio público:
> <https://github.com/protazoarium/farol-ss>.

---

## Checklist final

- [ ] Painel implantado, URL pública funcionando
- [ ] Logo 200×200 e 2–3 telas preparadas
- [ ] Etapa 1 (formulário CGU) enviada
- [ ] Reúso criado no dados.gov.br com **Visibilidade: Pública**
- [ ] Todos os conjuntos de dados de origem selecionados
- [ ] **"Enviar para homologação"** clicado; status = *pendente de homologação*
- [ ] Guardar o link público do reúso e o comprovante da Etapa 1

const { P, H1, H2, BUL, NUM, TABLE, BOX, GAP, build } = require("./lib");
const c = [];

c.push(BOX("Resumo", [
  "Este documento detalha as pendências técnicas citadas na seção 8 do esboço (documento 02). Todos os números foram conferidos em `data/gold/ieas.parquet` (925 município-anos: 185 municípios × 2020–2024) e no código de `src/farol_ss/index/` e `cli.py`.",
  "**Bloqueante para Resultados:** o ranque é calculado sobre a tabela empilhada. Recalcular por ano muda a cor do semáforo em **499 de 925** município-anos (54%).",
  "**Nada neste documento foi alterado no código.** As correções são propostas; a decisão de aplicá-las, e de como tratar o painel já publicado, é sua."], "FDE7E7"));
c.push(GAP());

c.push(H1("1. Ranque sobre a tabela empilhada (bloqueante)"));
c.push(P("`ieas` (cli.py) chama `calcular_ieas` uma única vez sobre todos os anos. Dentro dela, `rank_percentil` ranqueia as 925 linhas juntas. O ranque de um município em 2022 é, portanto, comparado com o dos outros anos, e o gap passa a medir mudanças de nível entre anos, não alinhamento entre municípios."));
c.push(TABLE(["Ano", "Média do ranque A", "Média do ranque N", "Gap médio", "Vermelho", "Azul"], [
  ["2020", "0,30", "0,40", "−0,09", "45", "15"],
  ["2021", "0,32", "0,47", "−0,15", "56", "9"],
  ["2022", "0,31", "0,62", "−0,32", "99", "6"],
  ["2023", "0,82", "0,48", "+0,34", "0", "86"],
  ["2024", "0,75", "0,53", "+0,22", "2", "60"]], [1100, 2000, 2000, 1500, 1519, 1519]));
c.push(GAP());
c.push(P("A causa do salto de 2023 é o nível de L1 (transferências sociais per capita): a mediana vai de R$ 945 em 2022 para R$ 2.227 em 2023 e R$ 2.170 em 2024, enquanto L2 varia pouco (R$ 471 → 504). Como o ranque é empilhado, todo município de 2023–2024 passa a ocupar a metade superior da distribuição de alocação (mediana do ranque A: 0,84 e 0,75, contra ≈ 0,30 em 2020–2022). L3 (PNCP), com mediana de R$ 18 a R$ 183, pesa pouco no nível, mas sua cobertura também muda (seção 2)."));
c.push(H2("Efeito da correção proposta"));
c.push(P("Calculando `rank(pct=True)` dentro de cada ano (`groupby('ano')`), o gap médio fica em ≈ 0,00 em todos os anos e a distribuição das cores fica estável:"));
c.push(TABLE(["Ano", "Vermelho", "Amarelo", "Verde", "Azul", "Cinza"], [
  ["2020", "37", "43", "67", "37", "1"],
  ["2021", "37", "42", "71", "34", "1"],
  ["2022", "30", "48", "75", "31", "1"],
  ["2023", "27", "48", "77", "32", "1"],
  ["2024", "28", "39", "93", "25", "0"]], [1100, 1700, 1700, 1700, 1700, 1738]));
c.push(GAP());
c.push(BUL("**Proposta:** em `calcular_necessidade` e `calcular_alocacao`, trocar `rank_percentil(x)` por `x.groupby(df['ano']).transform(rank_percentil)`. O mesmo vale para os subíndices (`montar_sub_epidemiologico`, e os ranks de saneamento e vulnerabilidade em `cli.py`), que hoje também são empilhados."));
c.push(BUL("**Consequência a declarar no artigo:** com ranque por ano, o gap médio é nulo por construção. O semáforo passa a ser uma medida relativa dentro do ano, e não permite dizer que a alocação melhorou ou piorou no estado. Isso precisa constar nos Métodos e nas Limitações."));
c.push(BUL("**Painel e relatório:** a série temporal e os textos que descrevem a virada de 2023 precisam ser revistos depois da correção. Isso afeta material já publicado para o concurso; avalie antes de alterar."));

c.push(H1("2. Eixo A com composição que muda a cada ano"));
c.push(P("`media_ponderada` renormaliza os pesos pelos componentes presentes. Em 2020 não há L3, então o eixo A é só L1 (0,35) e L2 (0,40), renormalizados para 0,47 e 0,53. Em 2024, com L3 em 157 municípios, é uma média de três componentes. A regra do cinza (cobertura ≥ 0,50) não barra isso: dois de três componentes dão 0,67."));
c.push(BUL("**Efeito:** o mesmo município pode mudar de ranque de alocação só porque o PNCP passou a cobri-lo."));
c.push(BUL("**Opções:** (a) restringir o artigo a 2022–2024, anos com L3 em mais da metade dos municípios; (b) calcular o eixo A sem L3 como análise principal e usar L3 como sensibilidade; (c) exigir os três componentes para não ser cinza (reduz muito a amostra: 0, 8, 102, 72 e 156 município-anos completos). Recomendo (b), por manter os 925 município-anos e deixar a composição constante."));

c.push(H1("3. L1 é proxy de transferência social"));
c.push(P("O repasse fundo a fundo (`/transferencias`) exige acesso gov.br elevado. O que entra em L1 é Bolsa Família/BPC por habitante. A correlação de Spearman entre `l1_per_capita` e `extrema_pobreza_por_mil_hab` é 0,35 nos 925 município-anos. Como a pobreza também compõe o eixo N, parte do eixo A mede necessidade, o que aproxima os dois ranques e reduz o gap."));
c.push(P("A mediana de L1 mais que dobra de 2022 para 2023, o que sugere mudança de política ou de metodologia de pagamento, não de alocação em saúde. Vale confirmar a causa na fonte antes de escrever a Discussão."));
c.push(BUL("**No artigo:** nomear L1 como “transferências sociais federais per capita”, nunca como “repasse de saúde”, e discutir o viés na seção de Limitações."));
c.push(BUL("**Sensibilidade:** refazer o IEAS sem L1 (pesos de L2 e L3 renormalizados) e informar a concordância das cores."));

c.push(H1("4. Saneamento é retrato de 2022"));
c.push(P("`saneamento_ano_referencia = 2022` para toda a série. O subíndice de saneamento (35% da necessidade) não varia no tempo. Declarar nos Métodos e não interpretar variação temporal do eixo N como mudança de saneamento."));

c.push(H1("5. Pesos e limiares sem sensibilidade"));
c.push(P("Os pesos (0,40/0,35/0,25 e 0,35/0,40/0,25) e os limiares (±0,10; ±0,33) estão em `conf/ieas.yml` por julgamento. Um revisor pedirá análise de sensibilidade (manual da OCDE sobre indicadores compostos, ficha N01 do documento 01)."));
c.push(TABLE(["Análise", "Como fazer", "O que relatar"], [
  ["Pesos", "Pesos iguais; ±20% em cada peso; 1.000 sorteios de pesos (Dirichlet)", "Concordância das cores e correlação de Spearman do gap com o caso-base"],
  ["Limiares", "±0,05 e ±0,15 / ±0,25 e ±0,40", "Proporção de município-anos que muda de cor"],
  ["Método de normalização", "Escore-z em vez de ranque percentil (ver Luiz et al., 2009 na revisão do SIPES)", "Concordância das cores"],
  ["Eixo A sem L1 e/ou sem L3", "Pesos renormalizados", "Concordância das cores"],
  ["Janela temporal", "2022–2024 apenas", "Estabilidade dos resultados"]], [2200, 4300, 3138]));

c.push(H1("6. Ordem sugerida de trabalho"));
for (const t of [
  "Decidir se o ranque passa a ser por ano (recomendado) e como tratar o painel e o relatório já publicados.",
  "Aplicar a correção em `index/` e `cli.py`, atualizar os testes e regenerar `ieas.parquet`.",
  "Decidir a janela e a composição do eixo A (seção 2).",
  "Implementar as análises de sensibilidade (seção 5) como comando do repositório, para que todo número do artigo seja regenerável.",
  "Só então escrever Resultados e Discussão."]) c.push(NUM(t));

build("../05-pendencias-tecnicas.docx", "Pendências técnicas antes dos Resultados", "Farol-SS — achados da leitura do código e dos dados do índice", c);

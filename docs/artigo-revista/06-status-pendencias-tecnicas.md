# Status das pendências técnicas (documento 05)

Atualizado em 21/11/2026. Resolvido = no código, nos testes e nos números do manuscrito.

| # | Pendência (doc. 05) | Situação | Onde |
|---|---|---|---|
| 1 | Ranque sobre a tabela empilhada | **Resolvido.** Ranque por ano em todos os subíndices e eixos; teste que reproduz o artefato do ranque empilhado. | `index/ieas.py`, `index/normalize.py`, `tests/test_ieas.py` |
| 2 | Eixo A com composição que muda por ano (PNCP) | **Resolvido.** Opção (b): L1 + L2 na análise principal; L3 na sensibilidade. Piso de 2 componentes mantém Fernando de Noronha cinza. | `conf/ieas.yml` (`componentes_no_indice`, `alocacao_min_componentes`) |
| 3 | L1 é proxy de transferência social | **Declarado e quantificado.** Chamado "transferências sociais federais per capita"; sensibilidade sem L1 (49,3% mudam de cor). O salto 2022→2023 está inteiro no Bolsa Família (R$ 284 mi → R$ 1,09 bi em junho; BPC ×1,2). Causa na fonte oficial (MDS) ainda a confirmar. | manuscrito §2.4 e §4; `resultados/variantes.csv` |
| 4 | Saneamento é retrato de 2022 | **Declarado** nos Métodos, Resultados e Limitações; sensibilidade sem o subíndice (48,3% mudam). | manuscrito |
| 5 | Pesos e limiares sem sensibilidade | **Resolvido.** `farol sensibilidade`: pesos iguais, ±20%, 1.000 sorteios de Dirichlet, limiares, normalização (z), composição dos eixos, PCA, desfecho posterior, municípios pequenos, efeito do PNCP. | `index/sensibilidade.py`, `resultados/*.csv` |
| 6 | Ordem sugerida de trabalho | Cumprida: correção → testes → parquet regenerado → sensibilidade como comando → Resultados. | — |

## Efeitos colaterais conhecidos (decisão do autor)

- **Detector 2 (resíduo de regressão) não sinaliza mais nenhum caso.** Com ranques em [0, 1] o corte (resíduo robusto ≤ −2 e ≥ 8 pontos) não é alcançável. Opções: recalibrar para o valor bruto per capita ou aposentar o detector. Hoje está ativo e vazio; o painel e o relatório descrevem isso.
- **Painel e relatório publicados** foram atualizados (920/925 com cor, ranque por ano, 743 alertas). O `relatorio-tecnico.html` foi corrigido no texto, mas não é gerado por script: conferir visualmente.
- Os documentos 02 e 05 (.docx) são fotografias anteriores à correção e **não** foram regerados; vale este arquivo como substituto.

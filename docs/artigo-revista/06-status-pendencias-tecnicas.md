# Status das pendências técnicas (documento 05)

Atualizado em 21/11/2026. Resolvido = no código, nos testes e nos números do manuscrito.

| # | Pendência (doc. 05) | Situação | Onde |
|---|---|---|---|
| 1 | Ranque sobre a tabela empilhada | **Resolvido.** Ranque por ano em todos os subíndices e eixos; teste que reproduz o artefato do ranque empilhado. | `index/ieas.py`, `index/normalize.py`, `tests/test_ieas.py` |
| 2 | Eixo A com composição que muda por ano (PNCP) | **Resolvido.** Opção (b): L1 + L2 na análise principal; L3 na sensibilidade. Piso de 2 componentes mantém Fernando de Noronha cinza. | `conf/ieas.yml` (`componentes_no_indice`, `alocacao_min_componentes`) |
| 3 | L1 é proxy de transferência social | **Declarado, quantificado e causa confirmada.** O salto 2022→2023 (3,8×) mistura mudança real (1,9×, de R$ 570 mi em jul/2022 a R$ 1,09 bi em jun/2023) e **quebra de série no Portal da Transparência**: R$ 160–230 por família em jun/2022 contra R$ 415–435 em jul/2022 (sem mudança no nº de famílias); o MDS informou R$ 402 de média em jun/2022. A competência de junho de 2022 subestima o valor. Trocar junho por julho só em 2022 muda a cor de 15,1% dos município-anos de 2022. | manuscrito §2.4 e §3.4; `resultados/l1_2022_*.csv`; `scripts/l1_checagem_2022.py` |
| 4 | Saneamento é retrato de 2022 | **Declarado** nos Métodos, Resultados e Limitações; sensibilidade sem o subíndice (48,3% mudam). | manuscrito |
| 5 | Pesos e limiares sem sensibilidade | **Resolvido.** `farol sensibilidade`: pesos iguais, ±20%, 1.000 sorteios de Dirichlet, limiares, normalização (z), composição dos eixos, PCA, desfecho posterior, municípios pequenos, efeito do PNCP. | `index/sensibilidade.py`, `resultados/*.csv` |
| 6 | Ordem sugerida de trabalho | Cumprida: correção → testes → parquet regenerado → sensibilidade como comando → Resultados. | — |

## Decisões e efeitos colaterais

- **Detector 2 recalibrado** (21/11/2026): ajuste log(R$ per capita) ~ necessidade por ano, z ≤ −2 e queda ≥ 20%; 22 alertas (10 municípios, todos moderados). A versão sobre ranques ficava em [−1, 1] e não alcançava o corte.
- **Decisão em aberto — competência de L1 em 2022.** A série principal usa junho em todos os anos, e junho de 2022 está antes da quebra de série do Portal. Adotar julho em 2022 corrige o nível, mas muda a cor de ~15% dos município-anos de 2022 e obriga a regerar `fato_municipio_ano`, o IEAS, a sensibilidade, as figuras e os números do manuscrito. Não foi feito sem sua decisão.
- **Painel e relatório publicados** foram atualizados (920/925 com cor, ranque por ano, 765 alertas). O `relatorio-tecnico.html` foi corrigido no texto, mas não é gerado por script: conferir visualmente.
- Os documentos 02 e 05 (.docx) são fotografias anteriores à correção e **não** foram regerados; vale este arquivo como substituto.

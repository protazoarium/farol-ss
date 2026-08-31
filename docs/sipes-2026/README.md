# Trabalho para o V SIPES 2026 — Farol-SS

Material para submeter o **Farol da Saúde & Saneamento (Farol-SS / Painel-SS)**
ao **V Simpósio Internacional de Pesquisa em Estilos de Vida & Saúde (SIPES)** —
Recife-PE, 25 a 27 de novembro de 2026.

## Arquivos

| Arquivo | O que é |
|---|---|
| `projeto-sipes-2026.docx` | **Projeto para construção do trabalho**: identificação, protocolo de revisão de literatura (bases, strings de busca, critérios, modelo de fichamento, bibliografia inicial), síntese da metodologia e dos resultados do Farol-SS, **rascunho do resumo** (parágrafo único, ~2.325 caracteres — limite 2.500), estrutura do pôster, cronograma alinhado às rodadas do evento, divisão de tarefas, checklist e riscos. Documento de planejamento da equipe, não o texto final. |
| `esboco-banner-sipes-2026.docx` | **Esboço do trabalho em formato de banner** — conteúdo do Farol-SS já redigido em rascunho, com a estrutura de pôster técnico-científico da **ABNT NBR 15437:2006** (seções numeradas 1–5), marcas `(AUTOR, ANO)` nos pontos de citação da revisão, legendas de figura e referências no padrão **NBR 6023:2018** (puxadas de `revisao/referencias.ris`). |
| `banner-sipes-2026-modelo.docx` | Modelo de pôster "em branco" (mesma diagramação, sem o texto de rascunho) — para começar do zero se preferir. Escala 1:3; final **90 × 120 cm, retrato**. Logo do V SIPES no cabeçalho (obrigatória). |
| `revisao/` | **Workflow reprodutível da revisão de literatura** — ver `revisao/README.md` e `revisao/RESULTADO.md`. Já executado: 24 artigos Qualis A/B (`referencias.ris`), 17 PDFs de acesso aberto baixados e o **fichamento em RIS** (`revisao/fichamento.ris`) com resumo, referência ABNT e modelos de citação direta/indireta. |
| `assets/sipes-logo.png` | Logomarca do evento (baixada de `sipes.com.br/files/logo.png` em 30/08/2026). |
| `assets/diagrama-ieas.png` | Diagrama de construção do IEAS, gerado do painel — Figura 1 do pôster. |
| `_build_*.py` | Scripts que regeram os `.docx` (requerem `python-docx`). |

## Normas do evento (fonte: <https://sipes.com.br/trabalhos>, consultado em 30/08/2026 — reconferir)

- **Resumo**: parágrafo único, sem seções, **máximo 2.500 caracteres com espaços**,
  contendo introdução, objetivos, metodologia, resultados e conclusões.
- **Título**: máximo 50 palavras, só a primeira letra maiúscula.
- **Palavras-chave**: exatamente 3, dos vocabulários **DeCS ou MeSH**. Definidas
  (DeCS): **Saneamento** [D012499]; **Alocação de Recursos** [D040841];
  **Gastos em Saúde** [D005102].
- **Autores**: até 6; o 1º autor só pode ser principal em um trabalho; submissão
  só pelo formulário on-line; trabalho **inédito**.
- **Pôster**: **120 × 90 cm**, **logomarca do evento obrigatória**, design livre,
  português ou inglês.
- **Rodadas de submissão**: 1ª até 30/07/2026 (resultado 30/08); 2ª até 30/08
  (resultado 30/09); 3ª até 30/09 (resultado 20/10).

## Como finalizar o pôster

1. Preencher os campos entre colchetes no `banner-sipes-2026-modelo.docx`.
2. Inserir a **Figura 2** (mapa coroplético do farol de PE para 2024) — exportar
   da página *Farol* do painel em PNG 300 dpi.
3. Gerar o **QR code** do painel (`https://farol-ss.streamlit.app`) e colocar no
   rodapé.
4. Redefinir o tamanho da página para **90 cm (largura) × 120 cm (altura)** ou
   exportar em PDF e ampliar 3×; conferir que as imagens ficam a ≥ 300 dpi.
5. Manter a logomarca do V SIPES no cabeçalho.

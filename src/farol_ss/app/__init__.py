"""Painel Streamlit do Farol-SS.

`Home.py` é o ponto de entrada (`make app`); cada arquivo em `pages/` vira
uma página na navegação lateral. Módulos sem prefixo de página (`tema.py`,
`dados.py`) são helpers compartilhados — carregam dado do gold/ e fixam a
paleta, para que nenhuma página repita SQL nem escolha cor solta.
"""

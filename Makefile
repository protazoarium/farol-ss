.PHONY: help install spike ingest silver gold ieas all app api test lint clean

help:
	@grep -E '^[a-z-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

install:  ## Cria o venv e instala tudo (base + pipeline + api + sus + dev)
	uv sync --all-extras

spike:    ## Sonda cada fonte federal e reporta cobertura real em PE
	uv run farol spike

ingest:   ## Baixa todas as fontes para data/bronze (idempotente)
	uv run farol ingest

silver:   ## Normaliza bronze -> silver (tipagem, cod_ibge, deflação)
	uv run farol silver

gold:     ## Monta o fato municipio x ano
	uv run farol gold

ieas:     ## Calcula o IEAS e os alertas
	uv run farol ieas

all: ingest silver gold ieas  ## Pipeline completo

app:      ## Sobe o painel Streamlit
	uv run streamlit run src/farol_ss/app/Home.py

api:      ## Sobe a API aberta (FastAPI)
	uv run uvicorn farol_ss.api.main:api --reload --port 8000

test:     ## Roda os testes
	uv run pytest -q

lint:     ## Formata e verifica
	uv run ruff format src tests && uv run ruff check --fix src tests

clean:    ## Limpa as camadas derivadas (preserva bronze)
	rm -rf data/silver/* data/gold/*

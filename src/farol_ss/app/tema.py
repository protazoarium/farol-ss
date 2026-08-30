"""Paleta e rótulos do painel — um lugar só para cor e texto.

A paleta do semáforo foi validada com o `validate_palette.js` da skill
dataviz (modo claro, superfície #fcfcfb, todos os pares): os quatro tons
cromáticos passam o piso de separação para daltonismo (ΔE ≥ 8 no pior par
protan/deutan) e o piso de visão normal (ΔE ≥ 15). O cinza é
deliberadamente acromático — é estado "sem dado", não uma categoria a mais —
e por isso a cor nunca aparece sozinha: toda página que colore o mapa
também mostra o rótulo na legenda, no tooltip e na tabela.

`gap = rank(A) − rank(N)` ∈ [−1, 1]. Negativo = alocação atrás da
necessidade (subalocação); positivo = à frente (sobrealocação). O verde no
meio é o alvo, não o topo de uma escala — por isso os nomes do semáforo, e
não um degradê contínuo.
"""

from __future__ import annotations

# --- Semáforo do farol (categórico, ordenado da pior à melhor alocação) ---
FAROL_ORDEM: list[str] = ["vermelho", "amarelo", "verde", "azul", "cinza"]

FAROL_COR: dict[str, str] = {
    "vermelho": "#c62828",  # subalocação severa: necessidade ≫ alocação
    "amarelo": "#ef6c00",  # subalocação leve
    "verde": "#00897b",  # alinhado (|gap| ≤ 0,10)
    "azul": "#1565c0",  # sobrealocação: alocação ≫ necessidade
    "cinza": "#9e9e9e",  # cobertura insuficiente — IEAS não calculado
}

FAROL_ROTULO: dict[str, str] = {
    "vermelho": "Necessidade não atendida",
    "amarelo": "Subalocação leve",
    "verde": "Alocação alinhada",
    "azul": "Alocação acima da necessidade",
    "cinza": "Sem dado suficiente",
}

# --- Rampa sequencial azul (magnitude contínua) — steps de references/palette.md
SEQ_AZUL: list[str] = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#104281"]

CINZA_SEM_DADO = "#e6e6e3"  # município fora da camada exibida
CONTORNO = "#8a8a86"

# --- Texto de apoio -------------------------------------------------------
AGRAVOS: dict[str, str] = {
    "deng": "Dengue",
    "chik": "Chikungunya",
    "zika": "Zika",
    "lept": "Leptospirose",
    "hepa": "Hepatite A",
    "esqu": "Esquistossomose",
}

CAMADAS: dict[str, str] = {
    "farol": "Farol (IEAS)",
    "sub_epidemiologico": "Necessidade — carga epidemiológica (rank percentil)",
    "l3_per_capita": "Alocação — compras de insumos L3 (R$/hab, PNCP)",
}


def cor_sequencial(valor: float, vmin: float, vmax: float) -> str:
    """Mapeia `valor` para um dos 5 tons da rampa azul. NaN → cinza sem-dado."""
    if valor is None or vmax <= vmin or valor != valor:  # noqa: PLR0124 (NaN check)
        return CINZA_SEM_DADO
    frac = (valor - vmin) / (vmax - vmin)
    idx = min(len(SEQ_AZUL) - 1, max(0, int(frac * len(SEQ_AZUL))))
    return SEQ_AZUL[idx]

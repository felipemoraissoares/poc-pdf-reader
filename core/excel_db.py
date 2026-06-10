"""
Módulo de acesso ao banco de dados em Excel (casos.xlsx e resultados.xlsx).
Cria os arquivos automaticamente se não existirem.
"""

import os
import pandas as pd
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

CASOS_PATH = DATA_DIR / "casos.xlsx"
RESULTADOS_PATH = DATA_DIR / "resultados.xlsx"

PAISES_PARCEIROS = [
    "Portugal", "Espanha", "Argentina", "EUA", "Reino Unido",
    "Rep. Tcheca", "Alemanha", "França", "Israel", "Itália",
    "Bélgica", "Holanda", "Uruguai", "Índia", "Coreia",
    "Emirados Árabes", "Áustria", "Suécia"
]

COLUNAS_CASOS = [
    "numero_material", "numero_lote", "numero_licenca",
    "pais_fornecedor", "pais_origem_licenca", "arquivo_pdf",
    "data_cadastro", "status"
]

COLUNAS_RESULTADOS = (
    ["material", "lote", "licenca", "pais_fornecedor", "data_analise"]
    + PAISES_PARCEIROS
    + ["resultado_geral", "analista"]
)


def _garantir_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def inicializar_excel():
    """Cria os arquivos Excel com cabeçalhos se ainda não existirem."""
    _garantir_data_dir()

    if not CASOS_PATH.exists():
        df = pd.DataFrame(columns=COLUNAS_CASOS)
        df.to_excel(CASOS_PATH, index=False)

    if not RESULTADOS_PATH.exists():
        df = pd.DataFrame(columns=COLUNAS_RESULTADOS)
        df.to_excel(RESULTADOS_PATH, index=False)


def carregar_casos() -> pd.DataFrame:
    """Retorna DataFrame com todos os casos cadastrados."""
    inicializar_excel()
    try:
        df = pd.read_excel(CASOS_PATH)
        return df
    except Exception:
        return pd.DataFrame(columns=COLUNAS_CASOS)


def salvar_caso(dados: dict) -> bool:
    """Adiciona um novo caso ao Excel. Retorna True se salvou com sucesso."""
    try:
        df = carregar_casos()
        dados["data_cadastro"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        dados["status"] = "Pendente"
        nova_linha = pd.DataFrame([dados])
        df = pd.concat([df, nova_linha], ignore_index=True)
        df.to_excel(CASOS_PATH, index=False)
        return True
    except Exception as e:
        print(f"Erro ao salvar caso: {e}")
        return False


def carregar_resultados() -> pd.DataFrame:
    """Retorna DataFrame com todos os resultados de análise."""
    inicializar_excel()
    try:
        df = pd.read_excel(RESULTADOS_PATH)
        return df
    except Exception:
        return pd.DataFrame(columns=COLUNAS_RESULTADOS)


def salvar_resultado(dados: dict) -> bool:
    """Adiciona ou atualiza um resultado de análise no Excel."""
    try:
        df = carregar_resultados()
        dados["data_analise"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Atualiza se já existir resultado para a mesma licença
        mask = df["licenca"] == dados.get("licenca", "")
        if mask.any():
            for col, val in dados.items():
                if col in df.columns:
                    df.loc[mask, col] = val
        else:
            nova_linha = pd.DataFrame([dados])
            df = pd.concat([df, nova_linha], ignore_index=True)

        df.to_excel(RESULTADOS_PATH, index=False)

        # Atualizar status no casos.xlsx
        _atualizar_status_caso(dados.get("licenca", ""), dados.get("resultado_geral", ""))
        return True
    except Exception as e:
        print(f"Erro ao salvar resultado: {e}")
        return False


def _atualizar_status_caso(numero_licenca: str, resultado: str):
    """Atualiza o campo status no casos.xlsx após análise."""
    try:
        df = carregar_casos()
        mask = df["numero_licenca"] == numero_licenca
        if mask.any():
            df.loc[mask, "status"] = resultado
            df.to_excel(CASOS_PATH, index=False)
    except Exception:
        pass


def caso_ja_existe(numero_licenca: str) -> bool:
    """Verifica se uma licença já foi cadastrada."""
    df = carregar_casos()
    return numero_licenca in df["numero_licenca"].values

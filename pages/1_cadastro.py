"""
Página 1 — Cadastro de Casos
Formulário para registrar novas licenças de exportação.
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.excel_db import salvar_caso, carregar_casos, caso_ja_existe
from core.ui import render_sidebar, page_header

st.set_page_config(
    page_title="Cadastro — Export Control",
    page_icon="✈",
    layout="wide",
)

render_sidebar()

PDFS_DIR = Path(__file__).parent.parent / "pdfs"
PDFS_DIR.mkdir(exist_ok=True)

PAISES = [
    "Portugal", "Espanha", "Argentina", "EUA", "Reino Unido",
    "Rep. Tcheca", "Alemanha", "França", "Israel", "Itália",
    "Bélgica", "Holanda", "Uruguai", "Índia", "Coreia",
    "Emirados Árabes", "Áustria", "Suécia",
]

page_header("Cadastro de Casos",
            "Registre uma nova licença de exportação para análise")

# ─── Formulário ───────────────────────────────────────────────────────────────
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("Nova Licença")

col1, col2 = st.columns(2)
with col1:
    numero_material = st.text_input(
        "Número do Material *",
        placeholder="Ex.: MAT-2024-001",
        help="Código do material no sistema"
    )
    numero_licenca = st.text_input(
        "Número da Licença *",
        placeholder="Ex.: LIC-PT-2024-0042",
        help="Identificador único da licença (usado como nome do arquivo PDF)"
    )
    pais_fornecedor = st.selectbox(
        "País do Fornecedor *",
        options=[""] + PAISES,
        help="País de onde vem o material"
    )

with col2:
    numero_lote = st.text_input(
        "Número do Lote *",
        placeholder="Ex.: LOTE-2024-007"
    )
    pais_origem_licenca = st.selectbox(
        "País de Origem da Licença *",
        options=[""] + PAISES,
        help="País emissor da licença de exportação"
    )
    arquivo_pdf = st.file_uploader(
        "PDF da Licença *",
        type=["pdf"],
        help="Upload do PDF (texto ou escaneado)"
    )

analista = st.text_input(
    "Nome do Analista",
    placeholder="Ex.: João Silva"
)
st.markdown("</div>", unsafe_allow_html=True)

# ─── Botão de cadastro ────────────────────────────────────────────────────────
cadastrar = st.button("Cadastrar Caso", use_container_width=False)

if cadastrar:
    erros = []
    if not numero_material.strip():  erros.append("Número do Material é obrigatório.")
    if not numero_lote.strip():      erros.append("Número do Lote é obrigatório.")
    if not numero_licenca.strip():   erros.append("Número da Licença é obrigatório.")
    if not pais_fornecedor:          erros.append("País do Fornecedor é obrigatório.")
    if not pais_origem_licenca:      erros.append("País de Origem da Licença é obrigatório.")
    if arquivo_pdf is None:          erros.append("O PDF da licença é obrigatório.")

    if erros:
        for e in erros:
            st.error(e)
    elif caso_ja_existe(numero_licenca.strip()):
        st.warning(f"Já existe um caso com a licença **{numero_licenca.strip()}**.")
    else:
        nome_arquivo = f"{numero_licenca.strip()}.pdf"
        caminho_pdf = PDFS_DIR / nome_arquivo
        try:
            with open(caminho_pdf, "wb") as f:
                f.write(arquivo_pdf.getbuffer())

            dados = {
                "numero_material":    numero_material.strip(),
                "numero_lote":        numero_lote.strip(),
                "numero_licenca":     numero_licenca.strip(),
                "pais_fornecedor":    pais_fornecedor,
                "pais_origem_licenca":pais_origem_licenca,
                "arquivo_pdf":        nome_arquivo,
                "analista":           analista.strip() or "—",
            }

            if salvar_caso(dados):
                st.success(f"Caso **{numero_licenca.strip()}** cadastrado com sucesso.")
            else:
                st.error("Erro ao salvar o caso. Tente novamente.")
        except Exception as e:
            st.error(f"Erro ao salvar o PDF: {e}")

st.divider()

# ─── Tabela de casos ──────────────────────────────────────────────────────────
st.subheader("Casos Cadastrados")
df = carregar_casos()

if df.empty:
    st.info("Nenhum caso cadastrado ainda.")
else:
    colunas = [c for c in [
        "numero_licenca", "numero_material", "numero_lote",
        "pais_fornecedor", "pais_origem_licenca", "data_cadastro", "status"
    ] if c in df.columns]
    df_view = df[colunas].copy()
    df_view.columns = [
        "Nº Licença", "Nº Material", "Nº Lote",
        "País Fornecedor", "País Licença", "Data Cadastro", "Status"
    ][:len(colunas)]
    st.dataframe(df_view, use_container_width=True, hide_index=True)
    st.caption(f"{len(df)} caso(s) cadastrado(s).")

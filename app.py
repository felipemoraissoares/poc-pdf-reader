"""
Export Control PoC — Embraer
Ponto de entrada principal. Exibe métricas gerais, tabela de casos e opção de reset.
"""

import streamlit as st
import pandas as pd
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.excel_db import inicializar_excel, carregar_casos, CASOS_PATH, RESULTADOS_PATH
from core.ui import render_sidebar, page_header

st.set_page_config(
    page_title="Export Control PoC — Embraer",
    page_icon="✈",
    layout="wide",
    initial_sidebar_state="expanded",
)

render_sidebar()
inicializar_excel()

# ─── Cabeçalho ────────────────────────────────────────────────────────────────
page_header("✈  Export Control PoC",
            "Validação de Licenças de Exportação · Embraer S.A.")

# ─── Métricas ─────────────────────────────────────────────────────────────────
df_casos = carregar_casos()
total      = len(df_casos)
aprovados  = int((df_casos["status"] == "Aprovado").sum())  if total else 0
reprovados = int((df_casos["status"] == "Reprovado").sum()) if total else 0
pendentes  = int((df_casos["status"] == "Pendente").sum())  if total else 0
revisao    = int((df_casos["status"] == "Revisar").sum())   if total else 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total de Casos", total)
c2.metric("Aprovados",  aprovados)
c3.metric("Reprovados", reprovados)
c4.metric("Pendentes",  pendentes)
c5.metric("Revisar",    revisao)

st.divider()

# ─── Tabela de casos ──────────────────────────────────────────────────────────
st.subheader("Casos Cadastrados")

if df_casos.empty:
    st.info("Nenhum caso cadastrado. Use **Cadastro de Casos** para começar.")
else:
    colunas = [c for c in [
        "numero_licenca", "numero_material", "numero_lote",
        "pais_fornecedor", "pais_origem_licenca", "data_cadastro", "status"
    ] if c in df_casos.columns]

    df_view = df_casos[colunas].copy()
    df_view.columns = [
        "Nº Licença", "Nº Material", "Nº Lote",
        "País Fornecedor", "País Licença", "Data Cadastro", "Status"
    ][:len(colunas)]

    st.dataframe(df_view, use_container_width=True, hide_index=True)

st.divider()

# ─── Zona de reset (POC) ──────────────────────────────────────────────────────
with st.expander("⚙  Configurações da PoC — Área de Reset"):
    st.warning(
        "**Atenção:** as ações abaixo são irreversíveis e apagam todos os dados da PoC. "
        "Use apenas quando precisar reiniciar os testes do zero."
    )

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.markdown("**Apagar apenas resultados**")
        st.caption("Mantém os casos cadastrados, remove análises salvas.")
        if st.button("Limpar Resultados", key="del_res"):
            st.session_state["confirmar_res"] = True

        if st.session_state.get("confirmar_res"):
            st.error("Confirma exclusão de todos os **resultados**?")
            cc1, cc2 = st.columns(2)
            with cc1:
                if st.button("Sim, apagar", key="conf_res"):
                    try:
                        RESULTADOS_PATH.unlink(missing_ok=True)
                        inicializar_excel()
                        st.session_state.pop("confirmar_res", None)
                        st.success("Resultados removidos.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")
            with cc2:
                if st.button("Cancelar", key="canc_res"):
                    st.session_state.pop("confirmar_res", None)
                    st.rerun()

    with col_b:
        st.markdown("**Apagar tudo (casos + resultados)**")
        st.caption("Remove casos, resultados e PDFs cadastrados.")
        if st.button("Limpar Tudo", key="del_all"):
            st.session_state["confirmar_all"] = True

        if st.session_state.get("confirmar_all"):
            st.error("Confirma exclusão de **todos os dados** incluindo PDFs?")
            ca1, ca2 = st.columns(2)
            with ca1:
                if st.button("Sim, apagar tudo", key="conf_all"):
                    try:
                        CASOS_PATH.unlink(missing_ok=True)
                        RESULTADOS_PATH.unlink(missing_ok=True)
                        pdfs_dir = Path(__file__).parent / "pdfs"
                        for arq in pdfs_dir.glob("*.pdf"):
                            arq.unlink(missing_ok=True)
                        inicializar_excel()
                        # Limpa session_state de análises em andamento
                        for k in ["analise_resultado", "analise_licenca",
                                  "validacoes_status", "val_licenca"]:
                            st.session_state.pop(k, None)
                        st.session_state.pop("confirmar_all", None)
                        st.success("Todos os dados removidos. PoC reiniciada.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")
            with ca2:
                if st.button("Cancelar", key="canc_all"):
                    st.session_state.pop("confirmar_all", None)
                    st.rerun()

    with col_c:
        st.markdown("**Limpar sessão ativa**")
        st.caption("Descarta análise em andamento na sessão atual.")
        if st.button("Limpar Sessão", key="del_sess"):
            for k in ["analise_resultado", "analise_licenca",
                      "validacoes_status", "val_licenca",
                      "confirmar_res", "confirmar_all"]:
                st.session_state.pop(k, None)
            st.success("Sessão limpa.")
            st.rerun()

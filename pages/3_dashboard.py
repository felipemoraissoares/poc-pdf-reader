"""
Página 3 — Dashboard
Visão por material: quais países parceiros estão cobertos pela licença atrelada.
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.excel_db import carregar_resultados, carregar_casos
from core.rules import PAISES_PARCEIROS
from core.ui import render_sidebar, page_header

st.set_page_config(
    page_title="Dashboard — Export Control",
    page_icon="✈",
    layout="wide",
)

render_sidebar()

# CSS adicional desta página
st.markdown("""
<style>
.kpi-card {
    background: white;
    border-radius: 10px;
    padding: 18px 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    text-align: center;
    height: 100%;
}
.kpi-valor { font-size: 2rem; font-weight: 700; margin: 6px 0 2px; }
.kpi-label {
    font-size: 0.72rem;
    color: #6B7280;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}
.section-title {
    font-size: 0.85rem;
    font-weight: 700;
    color: #003087;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    border-bottom: 2px solid #0047AB;
    padding-bottom: 6px;
    margin: 24px 0 14px;
}
.cov-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.8rem;
    background: white;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
.cov-table th {
    background: #003087;
    color: white;
    font-weight: 600;
    padding: 9px 8px;
    text-align: center;
    white-space: nowrap;
    font-size: 0.72rem;
    letter-spacing: 0.3px;
}
.cov-table th.col-meta {
    text-align: left;
    min-width: 100px;
}
.cov-table td {
    padding: 7px 8px;
    text-align: center;
    border-bottom: 1px solid #F1F5F9;
    white-space: nowrap;
}
.cov-table td.col-meta {
    text-align: left;
    color: #1E293B;
    font-weight: 500;
}
.cov-table tr:hover td { background: #F8FAFC; }

/* Status de resultado geral */
.cell-aprovado  { background:#DCFCE7; color:#166534; font-weight:700; border-radius:4px; padding:3px 6px; }
.cell-reprovado { background:#FEE2E2; color:#991B1B; font-weight:700; border-radius:4px; padding:3px 6px; }
.cell-revisar   { background:#FEF3C7; color:#92400E; font-weight:700; border-radius:4px; padding:3px 6px; }
.cell-pendente  { background:#F1F5F9; color:#475569; border-radius:4px; padding:3px 6px; }

/* Células de país */
.pais-cob  { background:#DCFCE7; color:#166534; font-size:1rem; }
.pais-nao  { background:#FEE2E2; color:#991B1B; font-size:1rem; }
.pais-na   { background:#F1F5F9; color:#9CA3AF; font-size:0.8rem; }

/* Resumo por país — barra de progresso */
.prog-bar-wrap { background:#E5E7EB; border-radius:4px; height:8px; overflow:hidden; margin-top:4px; }
.prog-bar-fill { height:100%; border-radius:4px; }
</style>
""", unsafe_allow_html=True)

PAISES_LISTA = list(PAISES_PARCEIROS.keys())

PAISES_FORNECEDORES = [
    "Portugal", "Espanha", "Argentina", "EUA", "Reino Unido",
    "Rep. Tcheca", "Alemanha", "França", "Israel", "Itália",
    "Bélgica", "Holanda", "Uruguai", "Índia", "Coreia",
    "Emirados Árabes", "Áustria", "Suécia",
]

# ─── Filtros na sidebar ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="border-top:1px solid #1E3A5F; margin:4px 0 12px;"></div>
    <div style="font-size:0.68rem; color:#334155; font-weight:700;
                letter-spacing:1.2px; padding:0 6px 8px; text-transform:uppercase;">
        Filtros
    </div>
    """, unsafe_allow_html=True)

    filtro_fornecedor = st.multiselect(
        "País Fornecedor", options=PAISES_FORNECEDORES, default=[],
        placeholder="Todos"
    )
    filtro_status = st.multiselect(
        "Resultado Geral",
        options=["Aprovado", "Reprovado", "Revisar"],
        default=[], placeholder="Todos"
    )
    filtro_pais = st.selectbox(
        "Mostrar apenas cobertos por",
        options=["— Todos —"] + PAISES_LISTA
    )

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    if st.button("Atualizar dados", use_container_width=True):
        st.rerun()

# ─── Cabeçalho ────────────────────────────────────────────────────────────────
page_header("Dashboard",
            "Cobertura de licenças por material e país parceiro")

# ─── Dados ────────────────────────────────────────────────────────────────────
df_res   = carregar_resultados()
df_casos = carregar_casos()

# Verifica presença de colunas mínimas
colunas_paises_presentes = [p for p in PAISES_LISTA if p in df_res.columns]

if df_res.empty:
    st.info("Nenhuma análise salva ainda. Realize análises na página **Análise de Licença**.")
    st.stop()

# Aplica filtros
df_f = df_res.copy()
if filtro_fornecedor:
    df_f = df_f[df_f["pais_fornecedor"].isin(filtro_fornecedor)]
if filtro_status:
    df_f = df_f[df_f["resultado_geral"].isin(filtro_status)]
if filtro_pais != "— Todos —" and filtro_pais in df_f.columns:
    df_f = df_f[df_f[filtro_pais] == "Coberto"]

# ─── KPIs ─────────────────────────────────────────────────────────────────────
total   = len(df_f)
aprov   = int((df_f["resultado_geral"] == "Aprovado").sum())  if total else 0
reprov  = int((df_f["resultado_geral"] == "Reprovado").sum()) if total else 0
revs    = int((df_f["resultado_geral"] == "Revisar").sum())   if total else 0
pend    = max(0, len(df_casos) - len(df_res["licenca"].dropna().unique())) if "licenca" in df_res.columns else 0
pct_ap  = round(aprov / total * 100) if total else 0

kpis = [
    ("Total Analisados", total,          "#0047AB"),
    ("Aprovados",        f"{aprov} ({pct_ap}%)", "#16A34A"),
    ("Reprovados",       reprov,         "#DC2626"),
    ("Revisar",          revs,           "#D97706"),
    ("Pendentes",        pend,           "#6B7280"),
]
cols = st.columns(5)
for col, (label, valor, cor) in zip(cols, kpis):
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-valor" style="color:{cor};">{valor}</div>
        </div>
        """, unsafe_allow_html=True)

# ─── Tabela principal: material × país parceiro ───────────────────────────────
st.markdown('<div class="section-title">Cobertura por Material e País Parceiro</div>',
            unsafe_allow_html=True)

if df_f.empty:
    st.info("Nenhum registro corresponde aos filtros aplicados.")
else:
    # Colunas meta
    colunas_meta = [c for c in ["licenca", "material", "lote",
                                "pais_fornecedor", "resultado_geral"]
                    if c in df_f.columns]
    cabecalhos_meta = {
        "licenca": "Licença", "material": "Material", "lote": "Lote",
        "pais_fornecedor": "Fornecedor", "resultado_geral": "Resultado",
    }

    def _cell_resultado(v):
        cls = {
            "Aprovado": "cell-aprovado", "Reprovado": "cell-reprovado",
            "Revisar":  "cell-revisar",  "Pendente":  "cell-pendente",
        }.get(str(v), "cell-pendente")
        return f'<span class="{cls}">{v}</span>'

    def _cell_pais(v):
        v = str(v)
        if v == "Coberto":
            return '<span class="pais-cob" title="Coberto">✓</span>'
        elif v == "Não coberto":
            return '<span class="pais-nao" title="Não coberto">✗</span>'
        return '<span class="pais-na">—</span>'

    # Abreviações dos países para caber na tabela
    abrev = {
        "Portugal": "PT", "Espanha": "ES", "Argentina": "AR",
        "EUA": "EUA", "Reino Unido": "UK", "Rep. Tcheca": "CZ",
        "Alemanha": "DE", "França": "FR", "Israel": "IL",
        "Itália": "IT", "Bélgica": "BE", "Holanda": "NL",
        "Uruguai": "UY", "Índia": "IN", "Coreia": "KR",
        "Emirados Árabes": "AE", "Áustria": "AT", "Suécia": "SE",
    }

    # Monta HTML da tabela
    th_meta = "".join(
        f'<th class="col-meta">{cabecalhos_meta.get(c, c)}</th>'
        for c in colunas_meta
    )
    th_paises = "".join(
        f'<th title="{p}">{abrev.get(p, p[:2])}</th>'
        for p in colunas_paises_presentes
    )

    linhas_html = ""
    for _, row in df_f.iterrows():
        tds_meta = ""
        for c in colunas_meta:
            val = row.get(c, "—")
            if c == "resultado_geral":
                tds_meta += f'<td class="col-meta">{_cell_resultado(val)}</td>'
            else:
                tds_meta += f'<td class="col-meta">{val}</td>'

        tds_paises = "".join(
            f'<td>{_cell_pais(row.get(p, "—"))}</td>'
            for p in colunas_paises_presentes
        )
        linhas_html += f"<tr>{tds_meta}{tds_paises}</tr>"

    html_tabela = f"""
    <div style="overflow-x:auto; margin-bottom:8px;">
    <table class="cov-table">
        <thead><tr>{th_meta}{th_paises}</tr></thead>
        <tbody>{linhas_html}</tbody>
    </table>
    </div>
    <div style="font-size:0.74rem; color:#94A3B8; margin-top:4px;">
        <span style="background:#DCFCE7;color:#166534;padding:1px 7px;border-radius:3px;margin-right:8px;">✓ Coberto</span>
        <span style="background:#FEE2E2;color:#991B1B;padding:1px 7px;border-radius:3px;margin-right:8px;">✗ Não coberto</span>
        <span style="background:#F1F5F9;color:#9CA3AF;padding:1px 7px;border-radius:3px;">— Não analisado</span>
    </div>
    """
    st.markdown(html_tabela, unsafe_allow_html=True)

# ─── Resumo por país parceiro ─────────────────────────────────────────────────
st.markdown('<div class="section-title">Resumo de Cobertura por País</div>',
            unsafe_allow_html=True)

if not df_f.empty and colunas_paises_presentes:
    n_cols = 6
    grupos = [colunas_paises_presentes[i:i+n_cols]
              for i in range(0, len(colunas_paises_presentes), n_cols)]

    for grupo in grupos:
        cols_res = st.columns(len(grupo))
        for col, pais in zip(cols_res, grupo):
            cobertos    = int((df_f[pais] == "Coberto").sum())
            nao_cobertos= int((df_f[pais] == "Não coberto").sum())
            total_p     = cobertos + nao_cobertos
            pct         = round(cobertos / total_p * 100) if total_p else 0
            cor_barra   = "#16A34A" if pct >= 70 else ("#D97706" if pct >= 40 else "#DC2626")

            with col:
                st.markdown(f"""
                <div class="card" style="padding:12px 14px;">
                    <div style="font-size:0.72rem;font-weight:700;color:#003087;
                                margin-bottom:6px;">{pais}</div>
                    <div style="display:flex;justify-content:space-between;
                                font-size:0.78rem;color:#374151;">
                        <span>{cobertos}/{total_p if total_p else '—'}</span>
                        <span style="font-weight:700;color:{cor_barra};">{pct}%</span>
                    </div>
                    <div class="prog-bar-wrap">
                        <div class="prog-bar-fill"
                             style="width:{pct}%;background:{cor_barra};"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
else:
    st.info("Sem dados de cobertura por país.")

# ─── Exportar ─────────────────────────────────────────────────────────────────
st.divider()
if st.button("Exportar tabela para Excel"):
    import io as _io
    buf = _io.BytesIO()
    df_f.to_excel(buf, index=False)
    st.download_button(
        label="Baixar Excel",
        data=buf.getvalue(),
        file_name="export_control_dashboard.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

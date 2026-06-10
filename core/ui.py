"""
Módulo de UI compartilhada: CSS global, sidebar e helpers de estilo.
Importado por todas as páginas para evitar duplicação e garantir consistência.
"""

import streamlit as st

# ─── CSS global ───────────────────────────────────────────────────────────────
GLOBAL_CSS = """
<style>
/* Remove a navegação automática que o Streamlit injeta para apps multipage */
div[data-testid="stSidebarNavContainer"],
div[data-testid="stSidebarNav"],
section[data-testid="stSidebarNav"],
ul[data-testid="stSidebarNavItems"] {
    display: none !important;
}

:root {
    --azul-escuro: #003087;
    --azul-medio: #0047AB;
    --azul-claro: #E8EEF7;
    --verde:   #16A34A;
    --vermelho:#DC2626;
    --amarelo: #D97706;
    --cinza:   #6B7280;
}

.stApp { background-color: var(--azul-claro); }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #001d5c 0%, #003087 50%, #0047AB 100%);
}
[data-testid="stSidebar"] * { color: #CBD5E1 !important; }

/* Links de navegação na sidebar */
[data-testid="stSidebar"] [data-testid="stPageLink"] a {
    color: #94A3B8 !important;
    font-size: 0.87rem;
    font-weight: 500;
    padding: 7px 10px;
    border-radius: 6px;
    display: block;
    text-decoration: none;
    transition: background 0.15s, color 0.15s;
    letter-spacing: 0.1px;
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
    background: rgba(255,255,255,0.09) !important;
    color: #E2E8F0 !important;
}
[data-testid="stSidebar"] [data-testid="stPageLink-active"] a {
    background: rgba(255,255,255,0.13) !important;
    color: #ffffff !important;
    font-weight: 600;
    border-left: 3px solid #60A5FA;
}

/* ── Cards e containers ── */
.card {
    background: white;
    border-radius: 10px;
    padding: 22px 24px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    margin-bottom: 16px;
}
.page-header {
    background: linear-gradient(90deg, #003087 0%, #0047AB 100%);
    color: white;
    padding: 18px 24px;
    border-radius: 10px;
    margin-bottom: 24px;
}
.page-header h2 { color: white; margin: 0; font-size: 1.35rem; }
.page-header p  { color: #94A3B8; margin: 5px 0 0; font-size: 0.82rem; }

/* ── Botões ── */
.stButton > button {
    background-color: var(--azul-medio);
    color: white;
    border: none;
    border-radius: 6px;
    font-weight: 600;
    transition: background 0.2s;
}
.stButton > button:hover  { background-color: var(--azul-escuro) !important; }
.stButton > button:active { background-color: var(--azul-escuro) !important; }

/* Botão destrutivo (reset) */
.btn-danger > button {
    background-color: #DC2626 !important;
    color: white !important;
}
.btn-danger > button:hover { background-color: #991B1B !important; }

/* ── Métricas ── */
[data-testid="metric-container"] {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 14px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

/* ── Tabelas ── */
.stDataFrame thead th {
    background-color: var(--azul-escuro) !important;
    color: white !important;
    font-weight: 600;
}
</style>
"""


def render_sidebar():
    """Injeta o CSS global e renderiza a sidebar corporativa padrão."""
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding:14px 0 22px;">
            <div style="font-size:2.2rem; line-height:1;">✈</div>
            <div style="font-weight:700; font-size:0.98rem; color:#E2E8F0;
                        letter-spacing:0.4px; margin-top:6px;">
                Export Control
            </div>
            <div style="font-size:0.71rem; color:#475569; margin-top:3px;">
                Prova de Conceito · Embraer
            </div>
        </div>
        <div style="border-top:1px solid #1E3A5F; margin:0 0 12px;"></div>
        <div style="font-size:0.68rem; color:#334155; font-weight:700;
                    letter-spacing:1.2px; padding:0 6px 8px;
                    text-transform:uppercase;">
            Navegação
        </div>
        """, unsafe_allow_html=True)

        st.page_link("app.py",                  label="Início")
        st.page_link("pages/1_cadastro.py",     label="Cadastro de Casos")
        st.page_link("pages/2_analise.py",      label="Análise de Licença")
        st.page_link("pages/3_dashboard.py",    label="Dashboard")

        st.markdown("""
        <div style="border-top:1px solid #1E3A5F; margin:16px 0 10px;"></div>
        <div style="font-size:0.68rem; color:#334155; text-align:center;">
            v1.0.0 · Offline
        </div>
        """, unsafe_allow_html=True)


def page_header(titulo: str, subtitulo: str = ""):
    """Renderiza o cabeçalho padrão de página."""
    sub_html = f"<p>{subtitulo}</p>" if subtitulo else ""
    st.markdown(f"""
    <div class="page-header">
        <h2>{titulo}</h2>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def status_badge(status: str) -> str:
    """Retorna HTML de badge colorido para um status."""
    estilos = {
        "Aprovado":   "background:#DCFCE7;color:#166534;",
        "Reprovado":  "background:#FEE2E2;color:#991B1B;",
        "Revisar":    "background:#FEF3C7;color:#92400E;",
        "Pendente":   "background:#F1F5F9;color:#475569;",
        "Coberto":    "background:#DCFCE7;color:#166534;",
        "Não coberto":"background:#FEE2E2;color:#991B1B;",
    }
    estilo = estilos.get(status, "background:#F1F5F9;color:#475569;")
    return (f'<span style="{estilo} padding:2px 10px; border-radius:10px;'
            f' font-size:0.78rem; font-weight:600;">{status}</span>')

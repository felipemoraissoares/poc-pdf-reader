"""
Página 2 — Análise de Licença
Pipeline de extração, bounding box e validação por país fornecedor.
"""

import streamlit as st
import streamlit.components.v1 as components
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.excel_db import carregar_casos, salvar_resultado
from core.extractor import (
    extrair_pdf, encontrar_bboxes_para_campos,
    renderizar_pagina_com_bboxes,
)
from core.rules import (
    obter_regras, verificar_regra_automatica,
    verificar_paises_cobertos, calcular_resultado_geral, PAISES_PARCEIROS,
)
from core.ui import render_sidebar, page_header

st.set_page_config(
    page_title="Análise — Export Control",
    page_icon="✈",
    layout="wide",
)

render_sidebar()

# CSS adicional específico desta página
st.markdown("""
<style>
.regra-card {
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 10px;
    background: white;
}
.regra-aprovado     { border-left: 4px solid #16A34A; }
.regra-reprovado    { border-left: 4px solid #DC2626; }
.regra-inconclusivo { border-left: 4px solid #D97706; }
.regra-manual       { border-left: 4px solid #6366F1; }
.trecho-pdf {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    padding: 9px 13px;
    font-family: monospace;
    font-size: 0.8rem;
    color: #334155;
    margin-top: 8px;
    white-space: pre-wrap;
}
.legenda-item { display:inline-flex; align-items:center; gap:5px; margin-right:14px; font-size:0.8rem; }
.legenda-cor  { width:13px; height:13px; border-radius:3px; display:inline-block; }
</style>
""", unsafe_allow_html=True)

PDFS_DIR = Path(__file__).parent.parent / "pdfs"

# ─── Animação do pipeline ─────────────────────────────────────────────────────
# O ícone de documento percorre cada etapa suavemente antes de avançar.
# getCenter() calcula a posição real de cada coluna após o layout ser renderizado,
# garantindo alinhamento independentemente da largura da tela.
PIPELINE_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: 'Segoe UI', system-ui, sans-serif;
    background: linear-gradient(135deg, #001a4d 0%, #003087 55%, #004ab0 100%);
    border-radius: 12px;
    padding: 24px 28px 20px;
    color: #CBD5E1;
    overflow: hidden;
}

.top-label {
    text-align: center;
    font-size: 0.68rem;
    letter-spacing: 1.8px;
    font-weight: 700;
    color: #334155;
    text-transform: uppercase;
    margin-bottom: 22px;
}

/* Grade das 5 etapas */
.stages {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 0;
    position: relative;
}

/* Linha conectora entre os ícones */
.stages::before {
    content: '';
    position: absolute;
    top: 27px;
    left: 10%;
    right: 10%;
    height: 2px;
    background: rgba(255,255,255,0.12);
    z-index: 0;
}

.stage {
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
    z-index: 1;
    opacity: 0.35;
    transition: opacity 0.6s ease, transform 0.6s ease;
}
.stage.active {
    opacity: 1;
    transform: scale(1.08);
}
.stage.done {
    opacity: 0.55;
}

.icon-ring {
    width: 54px;
    height: 54px;
    border-radius: 50%;
    border: 2px solid rgba(255,255,255,0.18);
    background: rgba(255,255,255,0.06);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.35rem;
    margin-bottom: 9px;
    transition: border-color 0.6s, background 0.6s, box-shadow 0.6s;
    position: relative;
}
.stage.active .icon-ring {
    border-color: #60A5FA;
    background: rgba(96,165,250,0.18);
    box-shadow: 0 0 18px rgba(96,165,250,0.45), 0 0 4px rgba(96,165,250,0.3);
}
.stage.done .icon-ring {
    border-color: rgba(52,211,153,0.5);
    background: rgba(52,211,153,0.12);
}

.stage-label {
    font-size: 0.68rem;
    font-weight: 600;
    text-align: center;
    line-height: 1.35;
    color: #64748B;
    letter-spacing: 0.2px;
    transition: color 0.5s;
}
.stage.active  .stage-label { color: #CBD5E1; }
.stage.done    .stage-label { color: #475569; }

/* Trilha do documento */
#doc-track {
    position: relative;
    height: 52px;
    margin: 14px 0 6px;
}

#doc-icon {
    position: absolute;
    top: 6px;
    font-size: 1.7rem;
    /* Posição inicial = centro da coluna 0 */
    left: calc(10% - 17px);
    transition: left 1.9s cubic-bezier(0.45, 0.05, 0.55, 0.95);
    filter: drop-shadow(0 2px 6px rgba(255,255,255,0.25));
    z-index: 5;
}

/* Barra de progresso */
#prog-track {
    height: 4px;
    background: rgba(255,255,255,0.1);
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 14px;
}
#prog-fill {
    height: 100%;
    width: 0%;
    background: linear-gradient(90deg, #60A5FA, #818CF8);
    border-radius: 4px;
    transition: width 1.9s ease;
}

#status-msg {
    text-align: center;
    font-size: 0.8rem;
    color: #475569;
    letter-spacing: 0.3px;
    min-height: 18px;
}
</style>
</head>
<body>
  <div class="top-label">Pipeline de Processamento</div>

  <div class="stages" id="stages">
    <div class="stage" id="s0">
      <div class="icon-ring">▣</div>
      <div class="stage-label">Base<br>OGTM</div>
    </div>
    <div class="stage" id="s1">
      <div class="icon-ring">⬆</div>
      <div class="stage-label">Carrega-<br>mento</div>
    </div>
    <div class="stage" id="s2">
      <div class="icon-ring">◎</div>
      <div class="stage-label">Extração<br>IA</div>
    </div>
    <div class="stage" id="s3">
      <div class="icon-ring">◈</div>
      <div class="stage-label">Valida-<br>ção</div>
    </div>
    <div class="stage" id="s4">
      <div class="icon-ring">▤</div>
      <div class="stage-label">Dash-<br>board</div>
    </div>
  </div>

  <div id="doc-track">
    <span id="doc-icon">📄</span>
  </div>

  <div id="prog-track"><div id="prog-fill"></div></div>
  <div id="status-msg">Aguardando início…</div>

<script>
(function () {
  const stageIds  = ['s0','s1','s2','s3','s4'];
  const mensagens = [
    'Acessando base OGTM…',
    'Carregando documento PDF…',
    'Extraindo texto com IA…',
    'Validando regras de controle…',
    'Consolidando resultados no dashboard…',
    '✓  Processamento concluído'
  ];
  const progressos = [20, 40, 60, 80, 100];

  const docIcon  = document.getElementById('doc-icon');
  const progFill = document.getElementById('prog-fill');
  const statusEl = document.getElementById('status-msg');
  const stagesEl = document.getElementById('stages');

  // Calcula a posição central de cada coluna da grade (5 colunas iguais)
  // O documento (largura ≈ 27px) é centralizado sobre cada etapa.
  function targetLeft(idx) {
    const trackW = stagesEl.offsetWidth;
    const colW   = trackW / 5;
    return Math.round(colW * idx + colW / 2 - 13.5); // 13.5 = metade do ícone
  }

  let step = 0;

  function avancar() {
    // Desativa etapa anterior
    if (step > 0) {
      const prev = document.getElementById(stageIds[step - 1]);
      if (prev) { prev.classList.remove('active'); prev.classList.add('done'); }
    }

    if (step < stageIds.length) {
      const curr = document.getElementById(stageIds[step]);
      if (curr) curr.classList.add('active');

      // Move o documento para o centro desta etapa
      docIcon.style.left = targetLeft(step) + 'px';

      progFill.style.width = progressos[step] + '%';
      statusEl.textContent = mensagens[step];

      step++;
      // Cada etapa fica visível entre 2 s e 3 s antes de avançar
      const pausa = 2000 + Math.random() * 1000;
      setTimeout(avancar, pausa);

    } else {
      // Etapa final: mantém a última ativa, exibe mensagem de conclusão
      statusEl.textContent = mensagens[mensagens.length - 1];
      statusEl.style.color = '#34D399';
    }
  }

  // Aguarda o layout ser renderizado antes de iniciar
  setTimeout(avancar, 400);
})();
</script>
</body>
</html>
"""


def _executar_analise(caminho_pdf, pais_fornecedor):
    """Executa extração, bounding boxes, validações e cobertura de países."""
    dados = extrair_pdf(str(caminho_pdf), pais_fornecedor)
    texto = dados.get("texto_completo", "")

    campos_interesse = {
        "Fornecedor":  [pais_fornecedor, "fornecedor", "supplier"],
        "Embraer":     ["Embraer"],
        "End User":    ["End User", "usuario final", "Utilizzatore Finale", "Endverwender"],
        "Licença":     ["Licença", "License", "Licence", "Licencia", "Genehmigung"],
        "País Destino":["Brazil", "Brasil", "Germany", "France"],
    }
    bboxes = encontrar_bboxes_para_campos(campos_interesse, dados)

    regras = obter_regras(pais_fornecedor)
    validacoes = []
    for regra in regras:
        if regra["tipo"] == "automatico":
            res = verificar_regra_automatica(regra, texto)
        else:
            res = {"status": "Inconclusivo", "trechos": [], "automatico": False}
        validacoes.append({**regra, **res, "status_analista": res["status"]})

    paises_cobertos = verificar_paises_cobertos(texto)

    return {
        "dados_extracao": dados,
        "bboxes":         bboxes,
        "validacoes":     validacoes,
        "paises_cobertos":paises_cobertos,
        "texto_completo": texto,
    }


# ─── Cabeçalho ────────────────────────────────────────────────────────────────
page_header("Análise de Licença",
            "Extração, validação e classificação de licenças de exportação")

# ─── Seleção de caso ──────────────────────────────────────────────────────────
df_casos = carregar_casos()
if df_casos.empty:
    st.warning("Nenhum caso cadastrado. Acesse **Cadastro de Casos** primeiro.")
    st.stop()

caso_sel  = st.selectbox("Selecione a licença para analisar",
                         options=df_casos["numero_licenca"].tolist())
linha     = df_casos[df_casos["numero_licenca"] == caso_sel].iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Material",        linha.get("numero_material", "—"))
c2.metric("Lote",            linha.get("numero_lote", "—"))
c3.metric("País Fornecedor", linha.get("pais_fornecedor", "—"))
c4.metric("Status Atual",    linha.get("status", "Pendente"))

caminho_pdf = PDFS_DIR / str(linha.get("arquivo_pdf", ""))
if not caminho_pdf.exists():
    st.error(f"PDF não encontrado: {caminho_pdf}")
    st.stop()

# ─── Botão de análise ─────────────────────────────────────────────────────────
iniciar = st.button("Analisar Licença")

if "analise_resultado" not in st.session_state:
    st.session_state["analise_resultado"] = None
if "analise_licenca" not in st.session_state:
    st.session_state["analise_licenca"] = None

if iniciar:
    anim = st.empty()
    with anim.container():
        # height = 310 para acomodar todo o HTML da animação
        components.html(PIPELINE_HTML, height=310, scrolling=False)

    with st.spinner("Processando documento…"):
        try:
            time.sleep(1.5)   # deixa a animação iniciar visivelmente
            resultado = _executar_analise(caminho_pdf, linha["pais_fornecedor"])
            st.session_state["analise_resultado"] = resultado
            st.session_state["analise_licenca"]   = caso_sel
            time.sleep(9)     # aguarda o ciclo completo da animação (5 etapas × ~2 s)
        except Exception as e:
            st.error(f"Erro durante a análise: {e}")
            st.stop()

    anim.empty()
    st.success("Análise concluída.")
    st.rerun()

# ─── Exibição dos resultados ──────────────────────────────────────────────────
resultado = st.session_state.get("analise_resultado")
if resultado is None or st.session_state.get("analise_licenca") != caso_sel:
    st.info("Selecione um caso e clique em **Analisar Licença** para iniciar.")
    st.stop()

dados_extracao = resultado["dados_extracao"]
bboxes         = resultado["bboxes"]
validacoes_raw = resultado["validacoes"]
paises_cobertos= resultado["paises_cobertos"]

# ── Documento anotado ─────────────────────────────────────────────────────────
st.divider()
st.subheader("Documento Anotado")

col_pdf, col_tab = st.columns([3, 2])
with col_pdf:
    img = renderizar_pagina_com_bboxes(str(caminho_pdf), bboxes, numero_pagina=1)
    if img:
        st.image(img, caption="Página 1 — campos destacados", use_container_width=True)
        # Legenda de cores
        cores = {b["campo"]: b["cor"] for b in bboxes}
        if cores:
            itens = "".join(
                f"<span class='legenda-item'>"
                f"<span class='legenda-cor' style='background:{cor};'></span>{campo}</span>"
                for campo, cor in cores.items()
            )
            st.markdown(f"<div style='margin-top:6px;'>{itens}</div>",
                        unsafe_allow_html=True)
    else:
        st.warning("Não foi possível renderizar a página do PDF.")

with col_tab:
    st.markdown("**Campos Extraídos**")
    if bboxes:
        import pandas as pd
        df_bb = pd.DataFrame([{
            "Campo":  b["campo"],
            "Trecho": b["texto"][:55] + ("…" if len(b["texto"]) > 55 else ""),
            "Pág.":   b["pagina"],
            "Conf.":  f"{b.get('confianca', 100)}%",
        } for b in bboxes])
        st.dataframe(df_bb, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum campo localizado com posição definida.")

    st.markdown(f"**Método:** `{dados_extracao.get('metodo','—')}`  "
                f"· **Tipo:** `{dados_extracao.get('tipo','—')}`")
    if dados_extracao.get("erro"):
        st.warning(f"Aviso: {dados_extracao['erro']}")

with st.expander("Ver texto completo extraído"):
    st.text_area("", value=resultado["texto_completo"],
                 height=240, label_visibility="collapsed")

# ── Validações por regra ──────────────────────────────────────────────────────
st.divider()
st.subheader(f"Validações — {linha['pais_fornecedor']}")

if not validacoes_raw:
    st.info("Sem regras configuradas para este país fornecedor.")
else:
    if ("validacoes_status" not in st.session_state
            or st.session_state.get("val_licenca") != caso_sel):
        st.session_state["validacoes_status"] = {
            v["id"]: v.get("status_analista", "Inconclusivo") for v in validacoes_raw
        }
        st.session_state["val_licenca"] = caso_sel

    for val in validacoes_raw:
        status_atual = st.session_state["validacoes_status"].get(val["id"], "Inconclusivo")
        icone = {"Aprovado": "✓", "Reprovado": "✗", "Inconclusivo": "—"}.get(status_atual, "—")
        classe = {"Aprovado": "aprovado", "Reprovado": "reprovado",
                  "Inconclusivo": "inconclusivo"}.get(status_atual, "inconclusivo")
        tipo_classe = "manual" if not val.get("automatico", True) else classe

        st.markdown(f"""
        <div class="regra-card regra-{tipo_classe}">
            <strong>{icone} {val['id']}</strong>
            &nbsp;<span style="font-size:0.74rem;color:#94A3B8;">
                {'Automático' if val.get('automatico', True) else 'Revisão manual'}
            </span>
            <div style="margin-top:6px;color:#1E293B;font-size:0.87rem;">
                {val['descricao']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        trechos = val.get("trechos", [])
        if trechos:
            with st.expander(f"Trechos encontrados ({len(trechos)})"):
                for t in trechos[:3]:
                    st.markdown(f"<div class='trecho-pdf'>…{t['trecho']}…</div>",
                                unsafe_allow_html=True)
        elif val.get("instrucao"):
            st.info(val["instrucao"])
        else:
            st.caption("Nenhum trecho correspondente encontrado no PDF.")

        ca, cr, ci, _ = st.columns([1, 1, 1, 4])
        with ca:
            if st.button("Aprovado",     key=f"ap_{val['id']}"):
                st.session_state["validacoes_status"][val["id"]] = "Aprovado"
                st.rerun()
        with cr:
            if st.button("Reprovado",    key=f"rp_{val['id']}"):
                st.session_state["validacoes_status"][val["id"]] = "Reprovado"
                st.rerun()
        with ci:
            if st.button("Inconclusivo", key=f"ic_{val['id']}"):
                st.session_state["validacoes_status"][val["id"]] = "Inconclusivo"
                st.rerun()

# ── Países parceiros cobertos ─────────────────────────────────────────────────
st.divider()
st.subheader("Cobertura por País Parceiro")

cols = st.columns(6)
for idx, (pais, status) in enumerate(paises_cobertos.items()):
    cor  = "#DCFCE7" if status == "Coberto" else "#FEE2E2"
    icone= "✓" if status == "Coberto" else "✗"
    cor_texto = "#166534" if status == "Coberto" else "#991B1B"
    with cols[idx % 6]:
        st.markdown(f"""
        <div style="background:{cor};border-radius:7px;padding:9px 6px;
                    text-align:center;margin:3px 0;font-size:0.78rem;">
            <span style="color:{cor_texto};font-weight:700;">{icone}</span><br>
            <strong style="color:#1E293B;font-size:0.75rem;">{pais}</strong>
        </div>
        """, unsafe_allow_html=True)

# ── Resultado geral e salvar ──────────────────────────────────────────────────
st.divider()

validacoes_final = []
for val in validacoes_raw:
    v = dict(val)
    v["status_analista"] = st.session_state["validacoes_status"].get(val["id"], "Inconclusivo")
    validacoes_final.append(v)

resultado_geral = calcular_resultado_geral(validacoes_final)
cor_res = {"Aprovado": "#16A34A", "Reprovado": "#DC2626", "Revisar": "#D97706"}.get(
    resultado_geral, "#6B7280")

st.markdown(f"""
<div style="background:white;border-radius:10px;padding:20px;
            border-left:5px solid {cor_res};box-shadow:0 1px 4px rgba(0,0,0,0.08);">
    <div style="font-size:0.74rem;color:#6B7280;font-weight:700;letter-spacing:0.8px;">
        RESULTADO GERAL
    </div>
    <div style="font-size:1.9rem;font-weight:700;color:{cor_res};margin-top:4px;">
        {resultado_geral}
    </div>
    <div style="font-size:0.78rem;color:#94A3B8;margin-top:4px;">
        Baseado em {len(validacoes_final)} validação(ões)
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("")
analista_nome = st.text_input("Analista responsável",
                              value=str(linha.get("analista", "")))

cs, cl = st.columns([1, 4])
with cs:
    if st.button("Salvar Resultado", use_container_width=True):
        dados_resultado = {
            "material":        linha.get("numero_material", ""),
            "lote":            linha.get("numero_lote", ""),
            "licenca":         caso_sel,
            "pais_fornecedor": linha.get("pais_fornecedor", ""),
            "resultado_geral": resultado_geral,
            "analista":        analista_nome,
        }
        dados_resultado.update(paises_cobertos)
        if salvar_resultado(dados_resultado):
            st.success("Resultado salvo.")
        else:
            st.error("Erro ao salvar o resultado.")
with cl:
    if st.button("Limpar Análise"):
        st.session_state["analise_resultado"] = None
        st.session_state["analise_licenca"]   = None
        st.rerun()

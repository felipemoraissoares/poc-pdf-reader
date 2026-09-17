# Preparação para Reunião — PoC Export Control (Embraer)

---

## 1. Visão geral do case

**Problema:** A equipe de compliance da Embraer precisa validar manualmente licenças de exportação recebidas de fornecedores internacionais — um processo repetitivo, sujeito a erro humano e dependente do conhecimento tácito de analistas sobre os padrões documentais de cada país.

**Objetivo:** Avaliar a viabilidade técnica de automatizar a extração de texto e a validação de regras em documentos PDF de licenças de exportação, usando NLP e OCR, e medir com rigor se essa automação é confiável o suficiente para ser levada a produção.

**Área envolvida:** Export Control / Compliance

**Resultado esperado:** Uma PoC funcional que demonstra o pipeline completo — do upload do PDF ao resultado de validação — e entrega métricas formais (precision, recall, F1, score de qualidade OCR) que fundamentam a decisão de investir ou não em um produto real.

---

## 2. Participação direta e decisões técnicas

O projeto foi desenvolvido de forma integral: arquitetura, código, estrutura de módulos, escolha de bibliotecas e design das regras de negócio.

Decisões técnicas sob responsabilidade direta:

- **EasyOCR no lugar de Tesseract/Poppler:** elimina instaladores externos e permite deploy 100% offline via `pip install`, reduzindo atrito de adoção em ambiente corporativo Windows.
- **Detecção automática de tipo de PDF (texto vs. imagem):** o sistema testa se a camada de texto nativa é suficiente (via pdfplumber) antes de acionar OCR — evita custo computacional desnecessário.
- **Dois métodos de extração em paralelo (NER neural com spaCy + Regex determinístico):** permite comparação formal entre abordagens, identificando onde cada uma se sai melhor sem fine-tuning específico.
- **Motor de regras por país fornecedor:** cada país tem um conjunto explícito de validações mapeado a partir dos requisitos reais de compliance da Embraer (EAR/ITAR para EUA, BAFA para Alemanha, SIEL/OIEL para UK, etc.).
- **Dataset sintético de 41 documentos JSON:** criado para viabilizar avaliação formal sem expor documentos reais, cobrindo 8 países × cenários válidos e inválidos.
- **Bootstrap para intervalos de confiança:** dado o volume reduzido de documentos reais disponíveis na PoC, foi implementado bootstrap (1.000 iterações) para comunicar a incerteza das métricas honestamente.

---

## 3. Fontes de dados, período e qualidade

**Fontes:**
- Documentos sintéticos: 41 JSONs gerados a partir das estruturas reais de licenças (Alemanha, Argentina, Coreia, Espanha, EUA, França — válidos e inválidos por país).
- Base de casos: `data/casos.xlsx` e `data/resultados.xlsx` — gerados em tempo de execução durante os testes da PoC.
- Regras de negócio: derivadas do conhecimento dos analistas de compliance da Embraer sobre os padrões documentais de 18 países parceiros.

**Período:** PoC desenvolvida e testada em 2025–2026.

**Limitações conhecidas:**
- Não foram usados documentos reais nesta fase — os sintéticos reproduzem a estrutura, mas não capturam todas as variações de layout encontradas no mundo real.
- OCR limitado a 5 páginas por documento (limite configurável) para manter performance aceitável em hardware sem GPU.
- Score OCR alto não garante extração semântica correta — um documento bem escaneado ainda pode ter campos em posições ou idiomas não cobertos pelas regras atuais.

**Cuidados de qualidade:**
- Intervalo de confiança por bootstrap em todas as métricas agregadas.
- Score composto de qualidade OCR (0–1) com classificação em 4 faixas (Excelente / Boa / Regular / Ruim).
- Cada palavra extraída pelo OCR carrega sua confiança individual (0–100%), usada para calcular a confiança média do documento.

---

## 4. Estruturação do problema, hipóteses e metodologia

**Estruturação:** O problema foi dividido em dois eixos independentes:
1. *Extração* — conseguir ler o conteúdo do PDF, seja via camada de texto nativa ou OCR.
2. *Validação* — dado o texto extraído, checar se as evidências exigidas por cada país estão presentes.

**Hipóteses consideradas:**
- H1: Regex é suficiente para termos regulatórios fixos (EAR, ITAR, BAFA); NER adicionaria valor apenas para entidades contextuais (end user, fornecedor, país de destino).
- H2: PDFs escaneados em baixa resolução são o principal gargalo — o sistema deve sinalizar esses casos para revisão manual em vez de produzir resultados silenciosamente errados.
- H3: Um motor de regras explícito por país é mais auditável e manutenível pela equipe de compliance do que um modelo caixa-preta.

**Metodologia:**
- Pipeline de extração: detecção de tipo → pdfplumber (texto nativo) ou EasyOCR (imagem) → estrutura de palavras com bounding boxes.
- NER (spaCy `xx_ent_wiki_sm`) + Regex rodando sobre o mesmo texto — comparação cruzada por tipo de entidade.
- Motor de regras aplicado sobre o texto completo — cada regra retorna status, trechos encontrados e score.
- Avaliação formal com precision, recall, F1, taxa de cobertura e taxa de concordância NER×Regex.
- Dataset sintético com rótulos conhecidos permite calcular métricas ground-truth.
- LOOCV implementado para estimativa de performance com N pequeno.

---

## 5. Análises exploratórias, tratamentos e variáveis relevantes

**Tratamentos aplicados:**
- Normalização case-insensitive em todas as buscas de termos.
- Escala 2× na renderização das páginas para OCR (melhora acurácia em documentos de baixa resolução).
- Cache de readers EasyOCR por conjunto de idiomas (evita recarregamento de modelos pesados entre análises).
- Deduplicação de entidades por tipo em regex (conjunto `vistos` por tipo de entidade).

**Variáveis/features extraídas por documento:**
- `tem_embraer` (bool): Embraer aparece como destinatário
- `tem_end_user` (bool): campo de end user presente
- `tem_data_validade` (bool): data detectada no documento
- `n_termos_regulatorios` (int): quantidade de siglas regulatórias distintas encontradas
- `n_paises_mencionados` (int): países de destino identificados
- `comprimento_texto`, `razao_texto_por_pagina`: sinais de volume
- `confianca_media_ocr`: média das confianças por palavra
- `idioma_detectado`: idioma inferido pelo langdetect
- `tipo_pdf`: "texto" (nativo) ou "imagem" (escaneado)

---

## 6. Estratégia de avaliação e métricas

**Baseline implícito:** processo manual atual — 100% humano, sem métricas formais de recall.

**Alternativas avaliadas:**
- NER puro (spaCy, modelo multilíngue `xx_ent_wiki_sm` sem fine-tuning)
- Regex puro (padrões determinísticos específicos do domínio)
- Combinação: os dois métodos em paralelo, com comparação cruzada

**Estratégia de validação:**
- Dataset sintético com ground truth conhecido (41 documentos, 8 países)
- Bootstrap (1.000 iterações, seed fixo) para intervalos de confiança a 95%
- LOOCV para estimativa de acurácia com N pequeno
- Taxa de concordância NER×Regex como proxy de confiança sem ground truth externo

**Métricas escolhidas:**
- Precision, Recall, F1 por tipo de entidade e por método
- Taxa de cobertura: % de tipos de entidade encontrados por ao menos uma ocorrência
- Taxa de concordância: % de tipos em que NER e regex chegam ao mesmo valor
- Score de qualidade OCR (0–1): confiança média (60%) + proporção de palavras boas (30%) + penalidade por volume mínimo (10%)

---

## 7. Principais resultados, impacto e aprendizados

**Resultados:**
- Pipeline completo operacional: do upload do PDF ao resultado de validação com evidências textuais em tela.
- OCR multilíngue funcional offline para 12 idiomas (Inglês, Português, Espanhol, Alemão, Francês, Italiano, Holandês, Hebraico, Árabe, Coreano, Hindi, Sueco).
- Motor de regras cobre 11 países fornecedores com regras explícitas (Portugal, Espanha, Argentina, EUA, Reino Unido, Rep. Tcheca, Alemanha, França, Israel, Itália, Bélgica, Holanda).
- Bounding boxes sobre o PDF renderizado permitem auditoria visual de onde cada termo foi encontrado.
- Cobertura de parceiros: o sistema verifica quais dos 18 países parceiros da Embraer estão mencionados em cada licença.

**Impacto potencial:** redução do tempo de triagem inicial de licenças — casos com todos os termos encontrados automaticamente podem ser aprovados mais rápido; casos inconclusivos são flagados para revisão humana focada.

**Limitações conhecidas:**
- Regras baseadas em presença de termos — não validam semântica (ex.: não verifica se a data de validade está dentro do prazo).
- NER sem fine-tuning no domínio — baixa precisão para entidades contextuais em documentos muito específicos.
- Sem integração com SAP (as validações IL-V2 e IL-V3 para Israel permanecem manuais).
- Performance OCR depende de hardware — sem GPU, documentos longos podem levar 30–120 s.

**Aprendizados:**
- Regex bate NER para termos regulatórios fixos (EAR, ITAR, BAFA) — o NER tende a ignorar siglas que não aparecem em corpora gerais.
- A maior fonte de incerteza é a qualidade do scan, não o motor de regras — documentos abaixo de 70 DPI geram extrações irreliáveis independente do método.
- Dados sintéticos com rótulos conhecidos são indispensáveis para medir o sistema formalmente; sem eles só se pode inspecionar manualmente.

---

## 8. Materiais de apoio disponíveis

| Material | Localização |
|---|---|
| Código-fonte completo | Repositório git `poc-export-control/` |
| Aplicação web (Streamlit) | `app.py` + `pages/` — roda localmente com `streamlit run app.py` |
| Módulo de extração PDF | `core/extractor.py` |
| Motor de regras por país | `core/rules.py` |
| NER + Regex | `core/ner.py` |
| Framework de avaliação | `core/evaluation.py` |
| Score de qualidade OCR | `core/ocr_quality.py` |
| Feature engineering | `core/features.py` |
| Dataset sintético (41 docs) | `data/sinteticos/` (JSON por país, válido e inválido) |
| Base de casos/resultados | `data/casos.xlsx`, `data/resultados.xlsx` |
| Documentação de setup | `README.md`, `SETUP.md` |
| Dashboard interativo | Página 3 da aplicação (`pages/3_dashboard.py`) |
| Página de avaliação formal | Página 4 da aplicação (`pages/4_avaliacao.py`) — NER vs Regex, qualidade OCR, dados sintéticos |

---

## 9. Competências demonstradas pelo projeto

| Competência | Como aparece no projeto |
|---|---|
| **NLP aplicado** | NER multilíngue com spaCy + Regex de domínio; comparação formal dos dois métodos |
| **OCR e processamento de documentos** | EasyOCR puro-Python offline, detecção automática de tipo PDF, bounding boxes |
| **Avaliação rigorosa de modelos** | Precision/Recall/F1, bootstrap para IC, LOOCV, taxa de concordância |
| **Engenharia de software** | Arquitetura modular, cache de modelos, testes com dados sintéticos, deploy offline |
| **Domínio de negócio** | Regras de export control por país (EAR/ITAR, BAFA, SIEL/OIEL, etc.) codificadas e auditáveis |
| **Produto de dados** | Aplicação web completa com cadastro, análise, dashboard e página de avaliação |
| **Comunicação de incerteza** | Bootstrap, IC 95%, score composto de qualidade com 4 faixas — nenhuma métrica apresentada sem contexto de confiança |

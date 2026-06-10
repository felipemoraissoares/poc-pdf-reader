# Export Control PoC — Embraer

Aplicação Streamlit para análise de licenças de exportação.
**100% offline após a instalação — sem instaladores externos, tudo via pip.**

---

## Requisitos

- Windows 10/11
- Python 3.10 ou superior (instalado pelo administrador ou via Microsoft Store)
- Acesso à internet **somente durante a instalação inicial**

> Não é necessário instalar Tesseract, Poppler, ou qualquer outro software além do Python.
> O OCR é feito pelo **EasyOCR**, biblioteca pura Python instalada via pip.

---

## Instalação (feita uma única vez, com internet)

### 1. Criar e ativar o ambiente virtual

```cmd
cd poc-export-control
python -m venv venv
venv\Scripts\activate
```

### 2. Instalar as dependências Python

```cmd
pip install -r requirements.txt
```

> O pacote `easyocr` instala automaticamente PyTorch e todas as suas dependências.
> O download pode levar alguns minutos dependendo da conexão.

### 3. Baixar os modelos de OCR

Este passo requer internet e precisa ser feito **apenas uma vez**.
Os modelos ficam salvos na pasta `models\easyocr\` do projeto.

```cmd
venv\Scripts\python.exe scripts\download_ocr_models.py
```

Modelos baixados (~300–500 MB no total):

| Grupo                          | Idiomas                          |
|-------------------------------|----------------------------------|
| Ocidental básico              | Inglês, Português, Espanhol      |
| Europa Central                | Alemão, Francês, Italiano        |
| Europa Norte                  | Holandês, Sueco                  |
| Semítico                      | Hebraico, Árabe                  |
| Asiático                      | Coreano, Hindi                   |

Após este passo, a aplicação funciona **completamente offline**.

---

## Executar a aplicação

```cmd
venv\Scripts\activate
streamlit run app.py
```

Acesse no navegador: **http://localhost:8501**

---

## Estrutura do projeto

```
poc-export-control/
├── app.py                   ← Tela inicial com métricas e tabela de casos
├── pages/
│   ├── 1_cadastro.py        ← Formulário + upload de PDF + lista de casos
│   ├── 2_analise.py         ← Animação pipeline + extração + bounding boxes + validações
│   └── 3_dashboard.py       ← KPI cards, gráfico, tabela de cobertura por país
├── core/
│   ├── extractor.py         ← Detecção de tipo PDF, pdfplumber, EasyOCR, bounding boxes
│   ├── rules.py             ← Motor de regras por país fornecedor + cobertura de parceiros
│   └── excel_db.py          ← Criação e leitura/escrita dos Excels
├── data/                    ← Criado automaticamente (casos.xlsx, resultados.xlsx)
├── pdfs/                    ← PDFs das licenças cadastradas
├── models/
│   └── easyocr/             ← Modelos OCR baixados pelo script de setup
├── scripts/
│   └── download_ocr_models.py  ← Script de pré-download (roda com internet, uma vez)
└── requirements.txt
```

---

## Fluxo de uso

1. **Cadastro** — registre um caso com metadados e faça upload do PDF da licença
2. **Análise** — selecione o caso, clique em "Analisar", revise as validações por regra e salve
3. **Dashboard** — acompanhe cobertura por país parceiro, status geral e filtre os dados

---

## Idiomas OCR suportados

| País Fornecedor         | Idiomas EasyOCR   |
|------------------------|-------------------|
| Portugal / Brasil       | pt + en           |
| Espanha / Argentina     | es + en           |
| EUA / Reino Unido / Rep. Tcheca | en       |
| Alemanha / Áustria      | de + en           |
| França / Bélgica        | fr + en           |
| Israel                  | he + en           |
| Itália                  | it + en           |
| Holanda                 | nl + en           |
| Coreia                  | ko + en           |
| Índia                   | hi + en           |
| Emirados Árabes         | ar + en           |
| Uruguai / Suécia        | es/sv + en        |

---

## Troubleshooting

**`ModuleNotFoundError: easyocr`**
Execute `pip install -r requirements.txt` com o ambiente virtual ativado.

**OCR lento no primeiro uso**
O EasyOCR carrega os modelos na memória na primeira chamada de cada sessão (~10–30 s).
Nas chamadas seguintes da mesma sessão é imediato (modelos ficam em cache).

**Modelos não encontrados / erro de download**
Rode novamente `venv\Scripts\python.exe scripts\download_ocr_models.py` com internet.
Os modelos ficam em `models\easyocr\` e são reutilizados nas próximas execuções.

**Excel corrompido**
Delete os arquivos `data\casos.xlsx` e `data\resultados.xlsx`.
Eles serão recriados automaticamente ao iniciar a aplicação.

**PDF ilegível / nenhum texto extraído**
Verifique se o PDF não está protegido por senha.
Para PDFs escaneados em baixa resolução (< 100 DPI), a acurácia do OCR pode ser reduzida.

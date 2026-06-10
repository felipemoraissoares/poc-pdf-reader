"""
Módulo de extração de texto de PDFs.
Detecta automaticamente se o PDF tem camada de texto ou é imagem.
Para PDFs imagem usa EasyOCR — puro Python, sem instaladores externos.
"""

import io
import fitz  # PyMuPDF — usado para renderizar páginas como imagem
import pdfplumber
import numpy as np
from PIL import Image, ImageDraw
import re
from pathlib import Path
from typing import Optional

# Modelos EasyOCR são armazenados dentro do projeto para facilitar deploy offline
_MODELS_DIR = str(Path(__file__).parent.parent / "models" / "easyocr")

# Cache de readers EasyOCR por conjunto de idiomas (carregar modelo é lento)
_ocr_readers: dict = {}

# Mapeamento de país do fornecedor para lista de idiomas EasyOCR
LANG_MAP: dict[str, list[str]] = {
    "Portugal":        ["pt", "en"],
    "Brasil":          ["pt", "en"],
    "Espanha":         ["es", "en"],
    "Argentina":       ["es", "en"],
    "EUA":             ["en"],
    "Reino Unido":     ["en"],
    "Rep. Tcheca":     ["en"],
    "Alemanha":        ["de", "en"],
    "Áustria":         ["de", "en"],
    "França":          ["fr", "en"],
    "Bélgica":         ["fr", "en"],
    "Israel":          ["he", "en"],
    "Itália":          ["it", "en"],
    "Holanda":         ["nl", "en"],
    "Coreia":          ["ko", "en"],
    "Índia":           ["hi", "en"],
    "Emirados Árabes": ["ar", "en"],
    "Uruguai":         ["es", "en"],
    "Suécia":          ["sv", "en"],
}

# Quantidade mínima de caracteres por página para considerar que há camada de texto
_LIMIAR_TEXTO = 50

# Número máximo de páginas processadas por OCR (limita tempo de espera na PoC)
_MAX_PAGINAS_OCR = 5


def _obter_reader(langs: list[str]):
    """
    Retorna um reader EasyOCR cacheado.
    O primeiro acesso carrega os modelos da pasta local (ou baixa se ainda não existir).
    """
    import easyocr  # importação tardia para não bloquear o import do módulo
    chave = tuple(sorted(langs))
    if chave not in _ocr_readers:
        Path(_MODELS_DIR).mkdir(parents=True, exist_ok=True)
        _ocr_readers[chave] = easyocr.Reader(
            list(langs),
            gpu=False,
            model_storage_directory=_MODELS_DIR,
            verbose=False,
        )
    return _ocr_readers[chave]


def detectar_tipo_pdf(caminho_pdf: str) -> str:
    """Retorna 'texto' se o PDF tem camada de texto, 'imagem' se é escaneado."""
    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            total_chars = 0
            for i in range(min(3, len(pdf.pages))):
                texto = pdf.pages[i].extract_text() or ""
                total_chars += len(texto.strip())
            if total_chars >= _LIMIAR_TEXTO:
                return "texto"
    except Exception:
        pass
    return "imagem"


def extrair_texto_pdfplumber(caminho_pdf: str) -> dict:
    """
    Extrai texto de PDFs com camada de texto usando pdfplumber.
    Retorna texto completo, palavras com posições e metadados por página.
    """
    resultado = {
        "texto_completo": "",
        "paginas": [],
        "palavras": [],
        "metodo": "pdfplumber",
    }
    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            for i, pagina in enumerate(pdf.pages):
                texto_pagina = pagina.extract_text() or ""
                resultado["texto_completo"] += texto_pagina + "\n"
                resultado["paginas"].append({
                    "numero": i + 1,
                    "texto": texto_pagina,
                    "largura": pagina.width,
                    "altura": pagina.height,
                })

                for palavra in (pagina.extract_words() or []):
                    resultado["palavras"].append({
                        "texto": palavra.get("text", ""),
                        "x0": palavra.get("x0", 0),
                        "y0": palavra.get("top", 0),
                        "x1": palavra.get("x1", 0),
                        "y1": palavra.get("bottom", 0),
                        "pagina": i + 1,
                        "confianca": 100,
                    })
    except Exception as e:
        resultado["erro"] = str(e)

    return resultado


def extrair_texto_ocr(caminho_pdf: str, langs: list[str]) -> dict:
    """
    Extrai texto de PDFs imagem usando EasyOCR (puro Python, sem binários externos).
    Páginas são renderizadas via PyMuPDF; o texto é extraído pelo EasyOCR.
    """
    resultado = {
        "texto_completo": "",
        "paginas": [],
        "palavras": [],
        "metodo": f"easyocr ({'+'.join(langs)})",
    }
    try:
        reader = _obter_reader(langs)
        doc = fitz.open(caminho_pdf)
        n_paginas = min(len(doc), _MAX_PAGINAS_OCR)

        for i in range(n_paginas):
            pagina_doc = doc[i]
            # Renderiza a página em alta resolução (escala 2×)
            mat = fitz.Matrix(2.0, 2.0)
            pix = pagina_doc.get_pixmap(matrix=mat)
            img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
            img_array = np.array(img)

            # EasyOCR retorna: [(bbox_4pts, texto, confiança), ...]
            ocr_resultados = reader.readtext(img_array, detail=1, paragraph=False)

            texto_pagina = ""
            for (bbox_pts, texto, confianca) in ocr_resultados:
                texto_pagina += texto + " "
                xs = [p[0] for p in bbox_pts]
                ys = [p[1] for p in bbox_pts]
                # Divide por 2 para voltar às coordenadas da página original (escala 1×)
                resultado["palavras"].append({
                    "texto": texto,
                    "x0": min(xs) / 2.0,
                    "y0": min(ys) / 2.0,
                    "x1": max(xs) / 2.0,
                    "y1": max(ys) / 2.0,
                    "pagina": i + 1,
                    "confianca": int(confianca * 100),
                })

            resultado["texto_completo"] += texto_pagina + "\n"
            resultado["paginas"].append({
                "numero": i + 1,
                "texto": texto_pagina,
                "largura": img.width / 2,
                "altura": img.height / 2,
            })

        doc.close()
    except Exception as e:
        resultado["erro"] = str(e)

    return resultado


def extrair_pdf(caminho_pdf: str, pais_fornecedor: str) -> dict:
    """
    Ponto de entrada principal.
    Detecta o tipo do PDF e escolhe o motor de extração adequado.
    """
    tipo = detectar_tipo_pdf(caminho_pdf)
    langs = LANG_MAP.get(pais_fornecedor, ["en"])

    if tipo == "texto":
        dados = extrair_texto_pdfplumber(caminho_pdf)
    else:
        dados = extrair_texto_ocr(caminho_pdf, langs)

    dados["tipo"] = tipo
    dados["lang"] = "+".join(langs)
    return dados


def buscar_termo_no_texto(termo: str, dados_extracao: dict,
                           ignorar_case: bool = True) -> list:
    """Busca um termo no texto extraído e retorna ocorrências com contexto."""
    flags = re.IGNORECASE if ignorar_case else 0
    ocorrencias = []

    for info_pagina in dados_extracao.get("paginas", []):
        texto = info_pagina.get("texto", "")
        for match in re.finditer(re.escape(termo), texto, flags):
            inicio = max(0, match.start() - 60)
            fim    = min(len(texto), match.end() + 60)
            ocorrencias.append({
                "termo": termo,
                "pagina": info_pagina["numero"],
                "contexto": texto[inicio:fim].strip(),
            })

    return ocorrencias


def encontrar_bboxes_para_campos(campos: dict, dados_extracao: dict) -> list:
    """
    Para cada campo de interesse, localiza as palavras no PDF que correspondem
    ao termo e retorna bounding boxes com metadados para renderização.
    """
    CORES = ["#e74c3c", "#2980b9", "#27ae60", "#8e44ad",
             "#f39c12", "#16a085", "#d35400", "#2c3e50"]
    bboxes = []
    palavras = dados_extracao.get("palavras", [])

    for idx, (nome_campo, termos) in enumerate(campos.items()):
        cor = CORES[idx % len(CORES)]
        if isinstance(termos, str):
            termos = [termos]

        for termo in termos:
            if not termo or len(termo) < 2:
                continue
            tokens = termo.lower().split()
            for i, palavra in enumerate(palavras):
                if not palavra["texto"].lower().startswith(tokens[0]):
                    continue
                # Verifica tokens subsequentes
                match = True
                ultimo = i
                for k, token in enumerate(tokens[1:], start=1):
                    if i + k < len(palavras) and palavras[i + k]["texto"].lower().startswith(token):
                        ultimo = i + k
                    else:
                        match = False
                        break
                if match:
                    x0 = min(palavras[j]["x0"] for j in range(i, ultimo + 1))
                    y0 = min(palavras[j]["y0"] for j in range(i, ultimo + 1))
                    x1 = max(palavras[j]["x1"] for j in range(i, ultimo + 1))
                    y1 = max(palavras[j]["y1"] for j in range(i, ultimo + 1))
                    bboxes.append({
                        "campo": nome_campo,
                        "texto": " ".join(palavras[j]["texto"] for j in range(i, ultimo + 1)),
                        "x0": x0, "y0": y0, "x1": x1, "y1": y1,
                        "pagina": palavra["pagina"],
                        "cor": cor,
                        "confianca": palavra.get("confianca", 100),
                    })
                    break  # primeiro match por termo é suficiente

    return bboxes


def renderizar_pagina_com_bboxes(caminho_pdf: str, bboxes: list,
                                  numero_pagina: int = 1,
                                  escala: float = 2.0) -> Optional[Image.Image]:
    """
    Renderiza uma página do PDF como imagem (via PyMuPDF) e desenha
    bounding boxes coloridos nos campos encontrados.
    Retorna objeto PIL Image pronto para exibição.
    """
    try:
        doc = fitz.open(caminho_pdf)
        numero_pagina = max(1, min(numero_pagina, len(doc)))
        pagina = doc[numero_pagina - 1]
        mat = fitz.Matrix(escala, escala)
        pix = pagina.get_pixmap(matrix=mat)
        img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGBA")
        overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)

        for bbox in bboxes:
            if bbox.get("pagina", 1) != numero_pagina:
                continue
            x0 = bbox["x0"] * escala
            y0 = bbox["y0"] * escala
            x1 = bbox["x1"] * escala
            y1 = bbox["y1"] * escala
            cor_hex = bbox.get("cor", "#e74c3c").lstrip("#")
            r, g, b = tuple(int(cor_hex[i:i+2], 16) for i in (0, 2, 4))
            draw.rectangle([x0, y0, x1, y1], outline=(r, g, b, 255), width=3)
            draw.rectangle([x0, y0, x1, y1], fill=(r, g, b, 60))

        resultado = Image.alpha_composite(img, overlay).convert("RGB")
        doc.close()
        return resultado
    except Exception as e:
        print(f"Erro ao renderizar página: {e}")
        return None

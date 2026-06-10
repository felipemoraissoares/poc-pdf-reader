"""
Pré-download dos modelos EasyOCR para uso offline.
Execute este script UMA VEZ com acesso à internet antes de implantar a aplicação.
Os modelos ficam armazenados em models/easyocr/ dentro do projeto.

Uso:
    venv\\Scripts\\python.exe scripts\\download_ocr_models.py
"""

import sys
from pathlib import Path

# Garante que o diretório raiz do projeto está no path
sys.path.insert(0, str(Path(__file__).parent.parent))

MODELOS_DIR = Path(__file__).parent.parent / "models" / "easyocr"
MODELOS_DIR.mkdir(parents=True, exist_ok=True)

# Agrupamento de idiomas para download eficiente
# EasyOCR compartilha o modelo base entre idiomas do mesmo alfabeto
GRUPOS_IDIOMAS = [
    ("Ocidental — inglês, português, espanhol",  ["en", "pt", "es"]),
    ("Ocidental — alemão, francês, italiano",     ["de", "fr", "it"]),
    ("Ocidental — holandês, sueco",               ["nl", "sv"]),
    ("Semítico — hebraico, árabe",                ["he", "ar"]),
    ("Asiático — coreano",                        ["ko"]),
    ("Asiático — hindi (devanágarī)",             ["hi"]),
]


def main():
    try:
        import easyocr
    except ImportError:
        print("ERRO: easyocr não está instalado. Execute: pip install easyocr")
        sys.exit(1)

    print("=" * 60)
    print("  Pré-download de modelos EasyOCR — Export Control PoC")
    print("=" * 60)
    print(f"  Destino: {MODELOS_DIR}")
    print()

    total = len(GRUPOS_IDIOMAS)
    erros = []

    for i, (descricao, langs) in enumerate(GRUPOS_IDIOMAS, start=1):
        print(f"[{i}/{total}] {descricao} ({', '.join(langs)})...")
        try:
            reader = easyocr.Reader(
                langs,
                gpu=False,
                model_storage_directory=str(MODELOS_DIR),
                verbose=True,
            )
            print(f"       OK\n")
            del reader
        except Exception as e:
            erros.append((descricao, str(e)))
            print(f"       ERRO: {e}\n")

    print("=" * 60)
    if not erros:
        print("  Todos os modelos baixados com sucesso!")
        print("  A aplicação pode ser usada offline a partir de agora.")
    else:
        print(f"  {len(erros)} grupo(s) com erro:")
        for desc, msg in erros:
            print(f"    • {desc}: {msg}")
        print()
        print("  Verifique a conexão e rode o script novamente.")
    print("=" * 60)


if __name__ == "__main__":
    main()

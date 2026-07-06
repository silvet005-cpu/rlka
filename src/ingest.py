"""
ingest.py — Extraccion, limpieza y chunking de los documentos PDF fuente.

Responsabilidad (ver Documentacion_Tecnica, seccion 3 y 7; ADR-003;
tarjeta de Trello "2 - Proceso y extraccion de contenido"):

1. Extraccion: lee el texto de cada PDF, pagina por pagina (PDF nativo,
   no escaneado — no requiere OCR).
2. Limpieza: normaliza espacios y saltos de linea sobrantes que deja
   la extraccion de PDF.
3. Chunking por tamano fijo (500-1000 caracteres) con solapamiento,
   respetando el limite de cada pagina.
4. Metadata por chunk: documento de origen, categoria, y numero de
   pagina — necesario para que el agente cite la fuente exacta
   (ver seccion 11 de Documentacion_Tecnica, dialogos de RoofKA).

NOTA IMPORTANTE sobre la herramienta de extraccion (hallazgo de
validacion, riesgo R-02 del Diagnostico_ASIS_TOBE_RLKA):
Se probaron 3 herramientas de extraccion (pdfplumber, PyMuPDF, y
pdftotext de poppler-utils). Tanto pdfplumber como PyMuPDF descartan
por completo la tabla de la Seccion 6 (Duracion de garantia por tipo
de trabajo) del documento de Warranty — es una limitacion real de
como esas librerias interpretan el layout de esa tabla especifica en
el PDF. Unicamente "pdftotext -layout" (herramienta de linea de
comandos, parte de poppler-utils) extrae la tabla correctamente. Por
eso este modulo usa pdftotext en vez de una libreria de Python pura.

Requisito de sistema: poppler-utils debe estar instalado en el
entorno donde corra este script.
- Google Colab: !apt-get install -y poppler-utils
- Servidor OCI (Ubuntu/Debian): sudo apt-get install -y poppler-utils
"""

import os
import re
import subprocess

CHUNK_SIZE = 800
CHUNK_OVERLAP = 150

CATEGORY_BY_FILENAME = {
    "politica_warranty_dummy.pdf": "Garantía",
    "manual_procedimientos_operativos_dummy.pdf": "Procedimientos Operativos",
    "politica_rrhh_dummy.pdf": "Recursos Humanos",
}


def extract_pages_from_pdf(pdf_path: str) -> list[tuple[int, str]]:
    """
    Extrae el texto de un PDF usando pdftotext (poppler-utils) en modo
    -layout, que preserva correctamente el contenido de tablas que
    otras librerias de Python (pdfplumber, PyMuPDF) descartan.

    Returns:
        Lista de tuplas (numero_de_pagina, texto_de_la_pagina).
    """
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", pdf_path, "-"],
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        raise RuntimeError(
            "No se encontro 'pdftotext'. Instala poppler-utils:\n"
            "  Colab: !apt-get install -y poppler-utils\n"
            "  Ubuntu/Debian: sudo apt-get install -y poppler-utils"
        )

    # pdftotext separa cada pagina con un caracter de salto de pagina (\f).
    raw_pages = result.stdout.split("\f")

    pages = []
    for i, page_text in enumerate(raw_pages, start=1):
        if page_text.strip():
            pages.append((i, page_text))
    return pages


def clean_text(text: str) -> str:
    """Colapsa espacios y saltos de linea repetidos."""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_page_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Divide el texto de una pagina en fragmentos de tamano fijo con solapamiento."""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end].strip())
        start = end - overlap
    return chunks


def load_and_chunk_documents(data_dir: str = "data/") -> list[dict]:
    """
    Procesa todos los PDFs de la carpeta data/: extrae (con pdftotext),
    limpia, y divide en chunks de tamano fijo. Cada chunk conserva
    metadata de trazabilidad (fuente, categoria, pagina).
    """
    all_chunks = []

    pdf_files = [f for f in os.listdir(data_dir) if f.lower().endswith(".pdf")]

    if not pdf_files:
        raise FileNotFoundError(
            f"No se encontraron archivos PDF en '{data_dir}'. "
            "Verifica que los 3 documentos fuente esten ahi (ver ADR-003)."
        )

    for filename in pdf_files:
        pdf_path = os.path.join(data_dir, filename)
        pages = extract_pages_from_pdf(pdf_path)

        if not pages:
            print(f"Advertencia: no se pudo extraer texto de '{filename}'.")
            continue

        category = CATEGORY_BY_FILENAME.get(filename.lower(), "General")
        document_chunks = []

        for page_number, page_text in pages:
            cleaned = clean_text(page_text)
            for chunk_content in chunk_page_text(cleaned):
                if chunk_content:
                    document_chunks.append({
                        "content": chunk_content,
                        "source": filename,
                        "category": category,
                        "page": page_number,
                    })

        all_chunks.extend(document_chunks)
        print(f"'{filename}' ({category}): {len(pages)} paginas -> {len(document_chunks)} chunks")

    return all_chunks


if __name__ == "__main__":
    chunks = load_and_chunk_documents()

    print(f"\nTotal de chunks generados: {len(chunks)}")

    if chunks:
        print("\n--- Ejemplo del primer chunk ---")
        print(f"Fuente: {chunks[0]['source']}")
        print(f"Categoria: {chunks[0]['category']}")
        print(f"Pagina: {chunks[0]['page']}")
        print(f"Contenido (primeros 300 caracteres):\n{chunks[0]['content'][:300]}...")

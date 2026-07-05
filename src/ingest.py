"""
ingest.py — Extraccion, limpieza y chunking de los documentos PDF fuente.

Responsabilidad (ver Documentacion_Tecnica, seccion 3 y 7; ADR-003;
tarjeta de Trello "2 - Proceso y extraccion de contenido"):

1. Extraccion: lee el texto de cada PDF, pagina por pagina (PDF nativo,
   no escaneado — no requiere OCR).
2. Limpieza: normaliza espacios y saltos de linea sobrantes que deja
   la extraccion de PDF.
3. Chunking por tamano fijo (500-1000 caracteres) con solapamiento,
   respetando el limite de cada pagina — esta es la estrategia mas
   confiable dada la calidad real de extraccion de estos PDFs (se
   evaluo tambien chunking por seccion logica, pero los encabezados
   numerados a veces quedan pegados al texto siguiente al extraerse
   del PDF, y los pasos numerados de los flujos operativos se
   confundian con encabezados — ver nota en el commit).
4. Metadata por chunk: documento de origen, categoria, y numero de
   pagina — necesario para que el agente cite la fuente exacta
   (ver seccion 11 de Documentacion_Tecnica, dialogos de RoofKA).
"""

import os
import re
import pdfplumber

# Tamano de chunk recomendado por la tarjeta del challenge: 500-1000 caracteres.
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150

# Categoria de cada documento, segun su nombre de archivo.
CATEGORY_BY_FILENAME = {
    "politica_warranty_dummy.pdf": "Garantía",
    "manual_procedimientos_operativos_dummy.pdf": "Procedimientos Operativos",
    "politica_rrhh_dummy.pdf": "Recursos Humanos",
}


def extract_pages_from_pdf(pdf_path: str) -> list[tuple[int, str]]:
    """
    Extrae el texto de un PDF, conservando el numero de pagina de cada
    fragmento (necesario para la metadata de trazabilidad).

    Returns:
        Lista de tuplas (numero_de_pagina, texto_de_la_pagina).
    """
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text:
                pages.append((i, text))
    return pages


def clean_text(text: str) -> str:
    """
    Limpieza basica del texto extraido: colapsa espacios y saltos de
    linea repetidos que suelen aparecer al extraer texto de PDF.
    """
    text = re.sub(r"[ \t]+", " ", text)          # espacios repetidos
    text = re.sub(r"\n{3,}", "\n\n", text)        # mas de 2 saltos de linea seguidos
    return text.strip()


def chunk_page_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Divide el texto de una pagina en fragmentos de tamano fijo, con
    solapamiento entre ellos para no cortar una idea a la mitad.
    """
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
    Procesa todos los PDFs de la carpeta data/: extrae, limpia, y
    divide en chunks de tamano fijo, devolviendo una sola lista con
    los chunks de los 3 documentos fuente. Cada chunk conserva
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
            print(f"Advertencia: no se pudo extraer texto de '{filename}'. "
                  f"Revisar si el PDF tiene texto seleccionable (no escaneado).")
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

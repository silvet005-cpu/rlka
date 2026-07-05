"""
ingest.py — Extraccion y chunking de los documentos PDF fuente.

Responsabilidad (ver Documentacion_Tecnica, seccion 3 y 7; ADR-003):
- Leer los PDFs en /data
- Extraer texto de cada uno
- Dividir el texto en fragmentos (chunks) manejables, con solapamiento,
  para que el vector store pueda indexarlos y recuperarlos con precision.

Cada chunk conserva metadata de su documento de origen (source), necesaria
para que el agente pueda citar la fuente exacta en cada respuesta
(ver seccion 11 de Documentacion_Tecnica — dialogos de RoofKA).
"""

import os
import pdfplumber


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extrae todo el texto de un archivo PDF, pagina por pagina.

    Args:
        pdf_path: ruta al archivo PDF.

    Returns:
        El texto completo del PDF como un solo string.
    """
    full_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:

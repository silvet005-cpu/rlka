# RLKA — RoofKA

Agente de IA que responde preguntas en lenguaje natural sobre documentacion interna de Roof Leopard Roofing Company (Warranty, Manual de Procedimientos Operativos, Politica de RRHH), usando arquitectura RAG (Retrieval-Augmented Generation).

## Descripcion

[TODO: completar tras finalizar el desarrollo]

## Arquitectura

[TODO: pegar diagrama_flujo_arquitectura.svg + tabla de capas — ver Diagnostico_ASIS_TOBE_RLKA]

## Tecnologias

- Python 3.11+
- pdfplumber (extraccion de PDF)
- FAISS / ChromaDB (vector store)
- Streamlit (interfaz)
- Oracle Cloud Infrastructure (despliegue)

## Instrucciones de ejecucion

```bash
pip install -r requirements.txt
cp .env.example .env  # completar con tus valores reales
streamlit run src/app.py
```

## Ejemplos de preguntas

[TODO: capturar tras validacion local — ver seccion 11 de Documentacion_Tecnica]

## Ejemplos de respuestas del agente

[TODO: capturar transcripciones reales de RoofKA]

## Capturas de pantalla y video

[TODO: agregar 2-3 capturas de la interfaz funcionando]
[TODO: agregar enlace a video corto mostrando el agente en uso — recomendado por el programa para mostrar el proyecto a la comunidad]

---
Documento de demostracion — Challenge Oracle Tech Builder / Alura ONE.

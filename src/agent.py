"""
agent.py — Logica RAG: recuperacion + prompt + llamada al LLM.

Persona del agente: RoofKA (ver ADR-004 y seccion 11 de Documentacion_Tecnica
para los dialogos previstos: saludo, respuesta con fuente, manejo de
preguntas fuera de alcance, razonamiento cruzado entre documentos).
"""

SALUDO_INICIAL = (
    "Hola! Soy RoofKA, tu asistente de consulta interna. "
    "Puedo responder preguntas basandome en los documentos de Warranty, "
    "Manual de Procedimientos Operativos y Politica de RRHH. "
    "En que puedo ayudarte hoy?"
)

FUERA_DE_ALCANCE = (
    "No tengo esa informacion en los documentos disponibles. "
    "Puedo ayudarte con preguntas sobre garantias, procedimientos "
    "operativos o politicas de RRHH."
)

def answer_question(question, vectorstore):
    # TODO: recuperar contexto relevante
    # TODO: construir prompt con contexto
    # TODO: llamar al LLM
    # TODO: manejar caso de "no informacion" -> FUERA_DE_ALCANCE
    raise NotImplementedError

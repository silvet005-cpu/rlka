"""
test_agent.py — Pruebas unitarias reales del agente RLKA.

Cubre las dos piezas de logica mas criticas de agent.py, sin depender
de la API de Cohere ni de un indice FAISS real (se usan mocks), para
que las pruebas corran rapido y sin credenciales:

1. construir_consulta_busqueda(): la expansion de consultas cortas
   (ver Log_Cambios_RLKA, hallazgo del 10-jul-2026 sobre "nomina" y
   "closeout").
2. answer_question(): el umbral de confianza que activa el fallback
   ANTES de llamar a Cohere, para evitar alucinaciones cuando no hay
   contexto suficiente (ver ADR-005 y SYSTEM_PROMPT_TEMPLATE).

Ejecutar con: pytest tests/test_agent.py -v
"""

import os
import sys

# COHERE_API_KEY se valida al importar agent.py (ver agent.py linea 39-45).
# Se fija un valor dummy ANTES del import para poder probar la logica
# de fallback sin necesitar una API key real ni hacer llamadas de red.
os.environ.setdefault("COHERE_API_KEY", "test-key-dummy-no-se-usa")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from unittest.mock import patch

import agent  # noqa: E402


# ---------------------------------------------------------------------
# construir_consulta_busqueda()
# ---------------------------------------------------------------------

def test_pregunta_corta_se_expande_con_prefijo():
    """
    Una pregunta de 1 palabra (ej. "nomina") debe expandirse con el
    prefijo "informacion sobre" antes del embedding de busqueda -- esta
    es la correccion real del bug donde "nomina" y "closeout" caian por
    debajo del umbral de confianza al buscarse como palabra suelta.
    """
    consulta, es_corta = agent.construir_consulta_busqueda("nómina")
    assert es_corta is True
    assert consulta == f"{agent.PREFIJO_EXPANSION_CONSULTA_CORTA} nómina"


def test_pregunta_larga_no_se_expande():
    """
    Una pregunta con mas de PALABRAS_PARA_BUSQUEDA_AMPLIADA palabras ya
    tiene suficiente "forma de oracion" para el modelo de embeddings, y
    no debe modificarse -- expandirla innecesariamente podria diluir el
    significado original de la pregunta.
    """
    pregunta_larga = "cuanto dura la garantia de un techo completo"
    consulta, es_corta = agent.construir_consulta_busqueda(pregunta_larga)
    assert es_corta is False
    assert consulta == pregunta_larga


def test_caso_limite_exactamente_tres_palabras_se_expande():
    """
    PALABRAS_PARA_BUSQUEDA_AMPLIADA = 3 usa '<=', asi que una pregunta
    de exactamente 3 palabras cae en el caso "corta" y SI se expande.
    Este caso limite es facil de romper con un '<' en vez de '<=' al
    editar el codigo, por eso se prueba explicitamente.
    """
    consulta, es_corta = agent.construir_consulta_busqueda("que es closeout")
    assert es_corta is True
    assert consulta == f"{agent.PREFIJO_EXPANSION_CONSULTA_CORTA} que es closeout"


def test_pregunta_vacia_no_rompe_la_funcion():
    """Caso borde: string vacio no debe lanzar una excepcion."""
    consulta, es_corta = agent.construir_consulta_busqueda("")
    assert es_corta is True  # "".split() == [], len 0 <= 3
    assert consulta == f"{agent.PREFIJO_EXPANSION_CONSULTA_CORTA} "


# ---------------------------------------------------------------------
# answer_question() — umbral de confianza / fallback anti-alucinacion
# ---------------------------------------------------------------------

def test_sin_resultados_activa_fallback_sin_llamar_a_cohere():
    """
    Si search() no devuelve ningun resultado, answer_question() debe
    responder con FUERA_DE_ALCANCE inmediatamente, SIN llamar a
    co.chat() -- este es el guardrail principal contra alucinaciones
    (ver ADR-005). Se mockea co.chat para confirmar que nunca se invoca.
    """
    with patch("agent.search", return_value=[]) as mock_search, \
         patch.object(agent.co, "chat") as mock_chat, \
         patch("agent._log_interaction"):
        respuesta = agent.answer_question("pregunta cualquiera", index=None, metadata=None)

    assert respuesta == agent.FUERA_DE_ALCANCE
    mock_search.assert_called_once()
    mock_chat.assert_not_called()


def test_similitud_debajo_del_umbral_activa_fallback():
    """
    Si el mejor resultado tiene un similarity_score por debajo de
    SIMILARITY_THRESHOLD (0.45), debe activarse el fallback sin llamar
    a Cohere -- incluso si search() SI devolvio resultados.
    """
    resultados_baja_confianza = [
        {"similarity_score": 0.30, "source": "Politica_RRHH_Dummy.pdf", "page": 2, "content": "..."},
    ]
    with patch("agent.search", return_value=resultados_baja_confianza), \
         patch.object(agent.co, "chat") as mock_chat, \
         patch("agent._log_interaction"):
        respuesta = agent.answer_question("pregunta fuera de alcance", index=None, metadata=None)

    assert respuesta == agent.FUERA_DE_ALCANCE
    mock_chat.assert_not_called()


def test_similitud_arriba_del_umbral_si_llama_a_cohere():
    """
    Caso contrario al anterior: si el mejor resultado SUPERA el umbral
    de confianza, el agente debe proceder a llamar a Cohere y devolver
    su respuesta (no el fallback). Se mockea la respuesta de Cohere
    para no depender de la red ni de una API key real.
    """
    resultados_alta_confianza = [
        {"similarity_score": 0.72, "source": "Politica_Warranty_Dummy.pdf", "page": 4, "content": "La garantia dura 10 anos."},
    ]

    class RespuestaFalsa:
        class message:
            content = [type("Texto", (), {"text": "La garantía dura 10 años según Politica_Warranty_Dummy.pdf, página 4."})()]

    with patch("agent.search", return_value=resultados_alta_confianza), \
         patch.object(agent.co, "chat", return_value=RespuestaFalsa()) as mock_chat, \
         patch("agent._log_interaction"):
        respuesta = agent.answer_question("cuanto dura la garantia", index=None, metadata=None)

    assert respuesta != agent.FUERA_DE_ALCANCE
    assert "10 años" in respuesta
    mock_chat.assert_called_once()


def test_pregunta_corta_amplia_top_k_en_la_llamada_a_search():
    """
    Para preguntas cortas, answer_question() debe llamar a search() con
    un top_k >= TOP_K_AMPLIADO (8), no con el valor por defecto (6) --
    esta es la mitigacion original para preguntas de pocas palabras
    (ver PALABRAS_PARA_BUSQUEDA_AMPLIADA en agent.py).
    """
    with patch("agent.search", return_value=[]) as mock_search, \
         patch.object(agent.co, "chat"), \
         patch("agent._log_interaction"):
        agent.answer_question("nómina", index=None, metadata=None, top_k=6)

    _, kwargs = mock_search.call_args
    assert kwargs["top_k"] >= agent.TOP_K_AMPLIADO

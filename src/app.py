"""
app.py — Interfaz Streamlit minima (funcional, no decorativa).

Responsabilidad (ver Documentacion_Tecnica seccion 6; tarjeta de
Trello "6 - Implementacion, interfaz y manutencion"):

- Input de pregunta + historial de conversacion en sesion.
- Indicacion clara de que se conversa con un agente de IA.
- Boton de feedback (positivo/negativo) en cada respuesta.
- Lista de documentos disponibles (transparencia de alcance).

Nota oficial del programa: la prioridad es funcionalidad, no diseno
(ver Documentacion_Tecnica, seccion 6). Esta UI es deliberadamente
simple.
"""

import json
from datetime import datetime, timezone

import streamlit as st

from vectorstore import load_vectorstore
from agent import answer_question, SALUDO_INICIAL

FEEDBACK_LOG_PATH = "feedback.jsonl"

st.set_page_config(page_title="RoofKA — RLKA", page_icon="🏠")


@st.cache_resource
def get_vectorstore():
    """Carga el indice FAISS y la metadata una sola vez por sesion del servidor."""
    return load_vectorstore()


def log_feedback(question: str, answer: str, feedback: str) -> None:
    """Registra el feedback del usuario (tarjeta 8 - registrar ejecucion)."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "answer": answer,
        "feedback": feedback,  # "positivo" o "negativo"
    }
    with open(FEEDBACK_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


index, metadata = get_vectorstore()

AVATAR_ROOFKA = "🏠"
AVATAR_USUARIO = "🙋"

EJEMPLOS_PREGUNTAS = [
    "¿Cuánto dura la garantía de un techo completo?",
    "¿Qué incluye el checklist de cierre de instalación?",
    "¿Cómo se clasifica un contratista independiente?",
]

st.title("RoofKA")
st.caption("⚠️ Estás conversando con un agente de inteligencia artificial, no con una persona.")

with st.sidebar:
    st.subheader("Documentos disponibles")
    st.markdown(
        "- Política de Garantía (Warranty)\n"
        "- Manual de Procedimientos Operativos\n"
        "- Política de Recursos Humanos y Compensación"
    )
    st.caption("RoofKA solo responde con base en estos 3 documentos, citando la fuente exacta.")

    st.divider()
    st.subheader("Preguntas de ejemplo")
    pregunta_ejemplo = None
    for ejemplo in EJEMPLOS_PREGUNTAS:
        if st.button(ejemplo, use_container_width=True):
            pregunta_ejemplo = ejemplo

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": SALUDO_INICIAL}]

for i, msg in enumerate(st.session_state.messages):
    avatar = AVATAR_ROOFKA if msg["role"] == "assistant" else AVATAR_USUARIO
    with st.chat_message(msg["role"], avatar=avatar):
        st.write(msg["content"])

pregunta = st.chat_input("Escribe tu pregunta sobre garantías, procedimientos o RRHH...") or pregunta_ejemplo

if pregunta:
    st.session_state.messages.append({"role": "user", "content": pregunta})
    with st.chat_message("user", avatar=AVATAR_USUARIO):
        st.write(pregunta)

    with st.chat_message("assistant", avatar=AVATAR_ROOFKA):
        with st.spinner("RoofKA está consultando los documentos..."):
            respuesta = answer_question(pregunta, index, metadata)
        st.write(respuesta)

        col1, col2, _ = st.columns([0.1, 0.1, 0.8])
        with col1:
            if st.button("👍", key=f"like_{len(st.session_state.messages)}"):
                log_feedback(pregunta, respuesta, "positivo")
                st.toast("¡Gracias por tu retroalimentación!")
        with col2:
            if st.button("👎", key=f"dislike_{len(st.session_state.messages)}"):
                log_feedback(pregunta, respuesta, "negativo")
                st.toast("Gracias, usaremos esto para mejorar a RoofKA.")

    st.session_state.messages.append({"role": "assistant", "content": respuesta})

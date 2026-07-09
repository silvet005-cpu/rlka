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

import base64
import json
import os
import re
from datetime import datetime, timezone

import streamlit as st


def _markdown_bold_to_html(text: str) -> str:
    """
    Convierte **negrita** de markdown a <strong> HTML. Necesario porque
    el texto se inserta dentro de un div con unsafe_allow_html=True, y
    el markdown simple (**texto**) generado por Cohere no se procesa
    automaticamente ahi dentro (aparecia literal con asteriscos).
    """
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)

# Puente de compatibilidad: en Streamlit Community Cloud, las API keys
# se configuran en "Secrets" (st.secrets), no en un archivo .env local.
# Si la key no esta ya en las variables de entorno, la tomamos de
# st.secrets y la exponemos como variable de entorno, para que
# agent.py (que usa os.getenv) funcione igual en ambos entornos.
if "COHERE_API_KEY" not in os.environ and "COHERE_API_KEY" in st.secrets:
    os.environ["COHERE_API_KEY"] = st.secrets["COHERE_API_KEY"]

from ingest import load_and_chunk_documents
from vectorstore import build_vectorstore
from agent import answer_question, SALUDO_INICIAL

FEEDBACK_LOG_PATH = "feedback.jsonl"

st.set_page_config(page_title="RoofKA — RLKA", page_icon="docs/roofka_avatar.png")


@st.cache_resource
def get_vectorstore():
    """
    Construye el indice FAISS a partir de los PDFs en data/ al iniciar
    la app. Se reconstruye desde los documentos fuente en vez de cargar
    un archivo .faiss pre-generado, ya que ese archivo binario no se
    versiona en el repositorio (ver .gitignore). Esto tambien garantiza
    que la app siempre refleje el contenido actual de data/.
    """
    chunks = load_and_chunk_documents()
    return build_vectorstore(chunks)


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

AVATAR_ROOFKA = "docs/roofka_avatar.png"
AVATAR_USUARIO = "docs/user_avatar.png"

PREGUNTAS_FRECUENTES = [
    "¿Cuánto dura la garantía de un techo completo?",
    "¿Qué incluye el checklist de cierre de instalación?",
    "¿Cómo se clasifica un contratista independiente?",
]

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;700&family=Inter:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    h1, h2, h3 {
        font-family: 'Baloo 2', sans-serif !important;
    }
    .block-container {
        padding-top: 1.5rem !important;
    }
    [data-testid="stChatMessage"] {
        margin-bottom: -0.6rem;
    }
    .roof-a {
        position: relative;
        display: inline-block;
    }
    .roof-a::before {
        content: '';
        position: absolute;
        top: -16px;
        left: 50%;
        transform: translateX(-50%);
        width: 0;
        height: 0;
        border-left: 11px solid transparent;
        border-right: 11px solid transparent;
        border-bottom: 13px solid #232628;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    "<h1 style='color:#EEAB59; font-size:44px; margin-bottom:0;'>"
    "RoofK<span class='roof-a'>A</span></h1>",
    unsafe_allow_html=True,
)
st.caption("Agente de inteligencia artificial para consultas sobre garantías, procedimientos operativos y RRHH.")

with open("docs/leopard_bg_tile.png", "rb") as f:
    _leopard_bg_b64 = base64.b64encode(f.read()).decode()

st.markdown(
    f"""
    <style>
    [data-testid="stSidebarContent"] {{
        background-image: url("data:image/png;base64,{_leopard_bg_b64}");
        background-repeat: repeat;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader("Documentos disponibles")
    st.markdown(
        "- Política de Garantía (Warranty) — *v1.1, jul 2026*\n"
        "- Manual de Procedimientos Operativos — *v1.1, jul 2026*\n"
        "- Política de Recursos Humanos y Compensación — *v1.0, jul 2026*"
    )
    st.caption("RoofKA solo responde con base en estos 3 documentos, citando la fuente exacta.")

    st.divider()
    st.subheader("Preguntas frecuentes")
    pregunta_frecuente = None
    for pregunta_faq in PREGUNTAS_FRECUENTES:
        if st.button(pregunta_faq, use_container_width=True, type="primary"):
            pregunta_frecuente = pregunta_faq

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": SALUDO_INICIAL}]

for i, msg in enumerate(st.session_state.messages):
    avatar = AVATAR_ROOFKA if msg["role"] == "assistant" else AVATAR_USUARIO
    bg_color = "#FDF5E8" if msg["role"] == "assistant" else "#232628"
    text_color = "#232628" if msg["role"] == "assistant" else "#FDF5E8"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(
            f"<div style='background:{bg_color}; color:{text_color}; "
            f"border-radius:10px; padding:12px 16px; font-size:15.5px; line-height:1.5;'>{_markdown_bold_to_html(msg['content'])}</div>",
            unsafe_allow_html=True,
        )

if len(st.session_state.messages) == 1:
    st.caption("👇 Prueba con una de las preguntas frecuentes en el panel izquierdo, o escribe la tuya abajo.")

pregunta = st.chat_input("Escribe tu pregunta sobre garantías, procedimientos o RRHH...") or pregunta_frecuente

if pregunta:
    st.session_state.messages.append({"role": "user", "content": pregunta})
    with st.chat_message("user", avatar=AVATAR_USUARIO):
        st.markdown(
            f"<div style='background:#232628; color:#FDF5E8; "
            f"border-radius:10px; padding:12px 16px; font-size:15.5px; line-height:1.5;'>{pregunta}</div>",
            unsafe_allow_html=True,
        )

    with st.chat_message("assistant", avatar=AVATAR_ROOFKA):
        with st.status("🔎 Buscando en los documentos disponibles...", expanded=False) as status:
            respuesta = answer_question(pregunta, index, metadata)
            status.update(label="Listo", state="complete", expanded=False)
        st.markdown(
            f"<div style='background:#FDF5E8; color:#232628; "
            f"border-radius:10px; padding:12px 16px; font-size:15.5px; line-height:1.5;'>{_markdown_bold_to_html(respuesta)}</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div style='margin-top:14px;'></div>", unsafe_allow_html=True)

        col1, col2, _ = st.columns([0.1, 0.1, 0.8])
        with col1:
            if st.button("👍", key=f"like_{len(st.session_state.messages)}", type="primary"):
                log_feedback(pregunta, respuesta, "positivo")
                st.toast("¡Gracias por tu retroalimentación!")
        with col2:
            if st.button("👎", key=f"dislike_{len(st.session_state.messages)}"):
                log_feedback(pregunta, respuesta, "negativo")
                st.toast("Gracias, usaremos esto para mejorar a RoofKA.")

    st.session_state.messages.append({"role": "assistant", "content": respuesta})

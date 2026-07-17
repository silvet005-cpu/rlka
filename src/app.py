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


# Paletas de tema centralizadas (v2.0 — mejoras UI/UX). Mantener TODOS
# los colores dependientes de tema en este unico diccionario evita
# duplicar valores hardcodeados en cada f-string de la interfaz.
THEMES = {
    False: {  # modo claro
        "app_bg": "#FDF5E8",
        "bubble_assistant_bg": "rgba(255, 255, 255, 0.55)",
        "bubble_assistant_border": "rgba(255, 255, 255, 0.6)",
        "bubble_assistant_text": "#232628",
        "bubble_user_bg": "rgba(238, 171, 89, 0.92)",
        "bubble_user_border": "rgba(238, 171, 89, 0.4)",
        "bubble_user_text": "#412402",
    },
    True: {  # modo oscuro
        "app_bg": "#14161A",
        "bubble_assistant_bg": "rgba(255, 255, 255, 0.06)",
        "bubble_assistant_border": "rgba(255, 255, 255, 0.12)",
        "bubble_assistant_text": "#F1EFE8",
        "bubble_user_bg": "rgba(238, 171, 89, 0.9)",
        "bubble_user_border": "rgba(238, 171, 89, 0.3)",
        "bubble_user_text": "#2B1600",
    },
}


def get_theme_css(dark: bool) -> str:
    """
    Devuelve el bloque <style> completo para el tema activo (claro u
    oscuro), incluyendo el efecto de vidrio esmerilado (glassmorphism)
    de las burbujas de chat via backdrop-filter. Centralizar esto aqui
    evita tener que duplicar colores en cada punto donde se renderiza
    un mensaje.
    """
    t = THEMES[dark]
    return f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-color: {t['app_bg']} !important;
    }}
    .chat-bubble {{
        border-radius: 12px;
        padding: 12px 16px;
        font-size: 15.5px;
        line-height: 1.5;
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 0.5px solid transparent;
    }}
    .chat-bubble-assistant {{
        background: {t['bubble_assistant_bg']};
        border-color: {t['bubble_assistant_border']};
        color: {t['bubble_assistant_text']};
    }}
    .chat-bubble-user {{
        background: {t['bubble_user_bg']};
        border-color: {t['bubble_user_border']};
        color: {t['bubble_user_text']};
    }}
    </style>
    """

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

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False


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

st.markdown(get_theme_css(st.session_state.dark_mode), unsafe_allow_html=True)

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
    st.caption("RoofKA es el asistente de Roof Leopard Roofing Company y solo responde con base en estos 3 documentos, citando la fuente exacta.")

    st.toggle("🌙 Modo oscuro", key="dark_mode")

    st.divider()
    st.subheader("Preguntas frecuentes")
    pregunta_frecuente = None
    for pregunta_faq in PREGUNTAS_FRECUENTES:
        if st.button(
            pregunta_faq,
            use_container_width=True,
            type="primary",
            disabled=st.session_state.get("procesando", False),
        ):
            pregunta_frecuente = pregunta_faq

    st.divider()

    # Tip y Registro de ejecucion van agrupados aqui, DESPUES de las
    # preguntas frecuentes: son herramientas secundarias/auxiliares, no
    # el flujo principal de uso, asi que se colocan al final para no
    # competir visualmente con los botones de FAQ (que usan
    # type="primary" y deben ganar la atencion primero). Ambos usan el
    # mismo emoji de referencia a la marca (leopardo) para verse
    # consistentes entre si.
    with st.expander("🐆 Tip: cómo preguntar mejor"):
        st.caption(
            "Para respuestas más precisas, incluye el tema específico — por ejemplo, "
            "*'garantía de un techo completo'* en vez de solo *'garantía'*, o "
            "*'checklist de cierre'* en vez de *'closeout'*. RoofKA entiende preguntas "
            "cortas, pero entre más contexto le des, más precisa será la respuesta."
        )

    # Descarga del log de ejecucion (tarjeta 8 - registrar ejecucion).
    # Agrupado en un expander, colapsado por defecto: es una herramienta
    # de auditoria/evidencia, no parte del flujo de uso normal del
    # agente, asi que no debe competir visualmente con las preguntas
    # frecuentes. El filesystem de Streamlit Community Cloud es efimero
    # (feedback.jsonl se pierde en cada redeploy), de ahi la necesidad
    # de poder bajarlo como evidencia antes de que eso pase.
    with st.expander("🐆 Registro de ejecución"):
        st.caption("Historial de preguntas calificadas por el usuario (👍/👎), usado como evidencia de ejecución en producción.")
        if os.path.exists(FEEDBACK_LOG_PATH):
            with open(FEEDBACK_LOG_PATH, "rb") as f:
                st.download_button(
                    "⬇️ Descargar feedback.jsonl",
                    data=f,
                    file_name="feedback.jsonl",
                    mime="application/jsonl",
                    use_container_width=True,
                )
        else:
            st.caption("Aún no hay preguntas calificadas en esta sesión del servidor.")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": SALUDO_INICIAL}]
if "feedback_dado" not in st.session_state:
    st.session_state.feedback_dado = True  # no hay respuesta nueva pendiente de calificar
if "procesando" not in st.session_state:
    st.session_state.procesando = False  # True mientras se espera la respuesta del agente
if "pregunta_pendiente" not in st.session_state:
    st.session_state.pregunta_pendiente = None

for i, msg in enumerate(st.session_state.messages):
    avatar = AVATAR_ROOFKA if msg["role"] == "assistant" else AVATAR_USUARIO
    bubble_class = "chat-bubble-assistant" if msg["role"] == "assistant" else "chat-bubble-user"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(
            f"<div class='chat-bubble {bubble_class}'>{_markdown_bold_to_html(msg['content'])}</div>",
            unsafe_allow_html=True,
        )

        # Botones de feedback (tarjeta 8 - registrar ejecucion).
        # Se colocan aqui, ligados a session_state, y NO dentro del
        # bloque "if pregunta:" de mas abajo: st.chat_input() solo
        # devuelve texto en la ejecucion donde se escribio, asi que en
        # la ejecucion disparada por el clic en 👍/👎 "pregunta" ya
        # vuelve a estar vacio y ese bloque completo se saltaria,
        # perdiendo el clic antes de llamar a log_feedback(). Al usar
        # una bandera en session_state, el boton se sigue mostrando
        # (y el clic si se procesa) en la ejecucion siguiente.
        es_ultimo_mensaje = i == len(st.session_state.messages) - 1
        if msg["role"] == "assistant" and es_ultimo_mensaje and not st.session_state.feedback_dado:
            st.markdown("<div style='margin-top:6px;'></div>", unsafe_allow_html=True)
            col1, col2, _ = st.columns([0.1, 0.1, 0.8])
            with col1:
                if st.button("👍", key=f"like_{i}", type="primary"):
                    log_feedback(st.session_state.messages[i - 1]["content"], msg["content"], "positivo")
                    st.session_state.feedback_dado = True
                    st.toast("¡Gracias por tu retroalimentación!")
                    st.rerun()
            with col2:
                if st.button("👎", key=f"dislike_{i}"):
                    log_feedback(st.session_state.messages[i - 1]["content"], msg["content"], "negativo")
                    st.session_state.feedback_dado = True
                    st.toast("Gracias, usaremos esto para mejorar a RoofKA.")
                    st.rerun()

if len(st.session_state.messages) == 1 and not st.session_state.procesando:
    st.caption("👇 Prueba con una de las preguntas frecuentes en el panel izquierdo, o escribe la tuya abajo.")

# Fase 1 — Envio: se limita a anotar la pregunta y bloquear la UI de
# inmediato (sin llamar todavia a answer_question, que es lo lento).
# Bloqueamos ANTES de procesar para que los botones/input ya se vean
# deshabilitados durante toda la espera de Cohere, no solo al final.
# Esto es lo que evita que una segunda pregunta se dispare mientras la
# primera sigue en curso (ver docs/Log_Cambios_RLKA.md).
pregunta_nueva = st.chat_input(
    "Escribe tu pregunta sobre garantías, procedimientos o RRHH...",
    disabled=st.session_state.procesando,
) or pregunta_frecuente

if pregunta_nueva and not st.session_state.procesando:
    st.session_state.messages.append({"role": "user", "content": pregunta_nueva})
    st.session_state.procesando = True
    st.session_state.pregunta_pendiente = pregunta_nueva
    st.rerun()

# Fase 2 — Procesamiento: corre en la ejecucion siguiente, con la UI ya
# bloqueada (botones e input deshabilitados) mientras se espera Cohere.
if st.session_state.procesando:
    with st.chat_message("assistant", avatar=AVATAR_ROOFKA):
        with st.status("🔎 Buscando en los documentos disponibles...", expanded=False) as status:
            respuesta = answer_question(st.session_state.pregunta_pendiente, index, metadata)
            status.update(label="Listo", state="complete", expanded=False)
        st.markdown(
            f"<div class='chat-bubble chat-bubble-assistant'>{_markdown_bold_to_html(respuesta)}</div>",
            unsafe_allow_html=True,
        )

    st.session_state.messages.append({"role": "assistant", "content": respuesta})
    st.session_state.feedback_dado = False  # respuesta nueva, aun sin calificar
    st.session_state.procesando = False
    st.session_state.pregunta_pendiente = None
    st.rerun()  # fuerza una ejecucion limpia: UI desbloqueada + botones de feedback consistentes

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

import requests
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
# Paleta unica (v2.0 — se decidio dejar la app exclusivamente en modo
# oscuro, ya que es el estilo que coincide con la referencia visual
# real; el toggle claro/oscuro se elimino para reducir complejidad).
THEME = {
    "app_bg": "#0D0F14",
    "widget_bg": "#1A1D24",
    "sidebar_bg": "#0A0C10",
    "bubble_assistant_bg": "rgba(255, 255, 255, 0.08)",
    "bubble_assistant_border": "rgba(255, 255, 255, 0.12)",
    "bubble_assistant_text": "#F1EFE8",
    "bubble_user_bg": "rgba(238, 171, 89, 0.92)",
    "bubble_user_border": "rgba(238, 171, 89, 0.3)",
    "bubble_user_text": "#2B1600",
    "chip_bg": "rgba(238, 171, 89, 0.15)",
    "chip_text": "#FAC775",
    "chip_border": "rgba(238, 171, 89, 0.3)",
    "timestamp_color": "rgba(241, 239, 232, 0.4)",
    "input_bg": "rgba(255, 255, 255, 0.05)",
    "input_border": "rgba(255, 255, 255, 0.12)",
}

# Textos de interfaz por idioma (v2.0 — selector ES/EN/PT). IMPORTANTE:
# esto traduce SOLO el texto fijo de la interfaz (etiquetas, botones,
# placeholders). NO traduce las preguntas frecuentes ni las respuestas
# del agente, ya que los 3 documentos fuente estan en espanol -
# traducir eso requeriria tocar agent.py y el prompt de Cohere, con
# mayor riesgo y consumo de la cuota trial. Ver Mejoras_Futuras_RLKA.md.
TEXTS = {
    "es": {
        "header_caption": "Agente de inteligencia artificial para consultas sobre garantías, procedimientos operativos y RRHH.",
        "docs_header": "Documentos disponibles",
        "docs_list": (
            "- Política de Garantía (Warranty) — *v1.1, jul 2026*\n"
            "- Manual de Procedimientos Operativos — *v1.1, jul 2026*\n"
            "- Política de Recursos Humanos y Compensación — *v1.0, jul 2026*"
        ),
        "docs_caption": "RoofKA es el asistente de Roof Leopard Roofing Company y solo responde con base en estos 3 documentos, citando la fuente exacta. Respuestas basadas únicamente en los documentos oficiales — consultas más rápidas, sin adivinar.",
        "faq_header": "Preguntas frecuentes",
        "faq_note": "Las preguntas frecuentes se envían en español, ya que los documentos fuente están en español.",
        "tip_header": "🐆 Tip: cómo preguntar mejor",
        "tip_body": (
            "Para respuestas más precisas, incluye el tema específico — por ejemplo, "
            "*'garantía de un techo completo'* en vez de solo *'garantía'*, o "
            "*'checklist de cierre'* en vez de *'closeout'*. RoofKA entiende preguntas "
            "cortas, pero entre más contexto le des, más precisa será la respuesta."
        ),
        "log_header": "🐆 Registro de ejecución",
        "log_caption": "Historial de preguntas calificadas por el usuario (👍/👎), usado como evidencia de ejecución en producción.",
        "log_empty": "Aún no hay preguntas calificadas en esta sesión del servidor.",
        "download_btn": "⬇️ Descargar feedback.jsonl",
        "admin_unset_warning": "⚠️ ADMIN_PASSWORD no configurada — descarga sin restricción en este entorno.",
        "admin_locked_caption": "🔒 Acceso restringido — solicita la clave al administrador de Roof Leopard.",
        "admin_password_label": "Clave de administrador",
        "admin_verify_btn": "Verificar",
        "admin_wrong_password": "Clave incorrecta.",
        "empty_state_caption": "👇 Prueba con una de las preguntas frecuentes en el panel izquierdo, o escribe la tuya abajo.",
        "chat_placeholder": "Escribe tu pregunta sobre garantías, procedimientos o RRHH...",
        "feedback_chip": "✓ ¡Gracias por tu feedback!",
        "toast_positivo": "¡Gracias por tu retroalimentación!",
        "toast_negativo": "Gracias, usaremos esto para mejorar a RoofKA.",
    },
    "en": {
        "header_caption": "AI assistant for questions about warranty, operating procedures, and HR policies.",
        "docs_header": "Available documents",
        "docs_list": (
            "- Warranty Policy — *v1.1, Jul 2026*\n"
            "- Operating Procedures Manual — *v1.1, Jul 2026*\n"
            "- HR & Compensation Policy — *v1.0, Jul 2026*"
        ),
        "docs_caption": "RoofKA is Roof Leopard Roofing Company's assistant and only answers based on these 3 documents, citing the exact source. Answers based only on the official documents — faster answers, no guessing.",
        "faq_header": "Frequently asked questions",
        "faq_note": "Frequently asked questions are sent in Spanish, since the source documents are in Spanish.",
        "tip_header": "🐆 Tip: how to ask better",
        "tip_body": (
            "For more precise answers, include the specific topic — for example, "
            "*'warranty for a full roof'* instead of just *'warranty'*, or "
            "*'closeout checklist'* instead of *'closeout'*. RoofKA understands short "
            "questions, but the more context you give it, the more accurate the answer."
        ),
        "log_header": "🐆 Execution log",
        "log_caption": "History of questions rated by the user (👍/👎), used as execution evidence in production.",
        "log_empty": "No rated questions in this server session yet.",
        "download_btn": "⬇️ Download feedback.jsonl",
        "admin_unset_warning": "⚠️ ADMIN_PASSWORD not configured — unrestricted download in this environment.",
        "admin_locked_caption": "🔒 Restricted access — request the password from the Roof Leopard administrator.",
        "admin_password_label": "Administrator password",
        "admin_verify_btn": "Verify",
        "admin_wrong_password": "Incorrect password.",
        "empty_state_caption": "👇 Try one of the frequent questions on the left panel, or type your own below.",
        "chat_placeholder": "Type your question about warranty, procedures, or HR...",
        "feedback_chip": "✓ Thanks for your feedback!",
        "toast_positivo": "Thanks for your feedback!",
        "toast_negativo": "Thanks, we'll use this to improve RoofKA.",
    },
    "pt": {
        "header_caption": "Agente de inteligência artificial para consultas sobre garantia, procedimentos operacionais e RH.",
        "docs_header": "Documentos disponíveis",
        "docs_list": (
            "- Política de Garantia (Warranty) — *v1.1, jul 2026*\n"
            "- Manual de Procedimentos Operacionais — *v1.1, jul 2026*\n"
            "- Política de RH e Compensação — *v1.0, jul 2026*"
        ),
        "docs_caption": "RoofKA é o assistente da Roof Leopard Roofing Company e responde apenas com base nesses 3 documentos, citando a fonte exata. Respostas baseadas somente nos documentos oficiais — consultas mais rápidas, sem adivinhar.",
        "faq_header": "Perguntas frequentes",
        "faq_note": "As perguntas frequentes são enviadas em espanhol, já que os documentos fonte estão em espanhol.",
        "tip_header": "🐆 Dica: como perguntar melhor",
        "tip_body": (
            "Para respostas mais precisas, inclua o tema específico — por exemplo, "
            "*'garantia de um telhado completo'* em vez de apenas *'garantia'*, ou "
            "*'checklist de encerramento'* em vez de *'closeout'*. O RoofKA entende "
            "perguntas curtas, mas quanto mais contexto você der, mais precisa será a resposta."
        ),
        "log_header": "🐆 Registro de execução",
        "log_caption": "Histórico de perguntas avaliadas pelo usuário (👍/👎), usado como evidência de execução em produção.",
        "log_empty": "Ainda não há perguntas avaliadas nesta sessão do servidor.",
        "download_btn": "⬇️ Baixar feedback.jsonl",
        "admin_unset_warning": "⚠️ ADMIN_PASSWORD não configurada — download sem restrição neste ambiente.",
        "admin_locked_caption": "🔒 Acesso restrito — solicite a senha ao administrador da Roof Leopard.",
        "admin_password_label": "Senha do administrador",
        "admin_verify_btn": "Verificar",
        "admin_wrong_password": "Senha incorreta.",
        "empty_state_caption": "👇 Experimente uma das perguntas frequentes no painel esquerdo, ou digite a sua abaixo.",
        "chat_placeholder": "Digite sua pergunta sobre garantia, procedimentos ou RH...",
        "feedback_chip": "✓ Obrigado pelo seu feedback!",
        "toast_positivo": "Obrigado pelo seu feedback!",
        "toast_negativo": "Obrigado, vamos usar isso para melhorar o RoofKA.",
    },
}


def get_theme_css(hero_bg_b64: str) -> str:
    """
    Devuelve el bloque <style> completo del tema (unico, oscuro),
    incluyendo el efecto de vidrio esmerilado (glassmorphism) de las
    burbujas de chat via backdrop-filter. Centralizar esto aqui evita
    tener que duplicar colores en cada punto donde se renderiza un
    mensaje.

    IMPORTANTE sobre el fondo panoramico: se aplica a
    [data-testid="stAppViewContainer"] (el "cascaron" estable de la
    app), NUNCA a .block-container. El block-container es el
    contenido scrolleable que CRECE con cada mensaje nuevo del chat;
    aplicarle ahi un "background-size: cover" hacia que el calculo se
    hiciera contra una altura cada vez mayor, produciendo un recorte
    feo (una franja de color solido) en vez de la foto completa.
    stAppViewContainer, en cambio, mantiene el tamano del viewport sin
    importar cuanto crezca el historial de conversacion.
    """
    t = THEME
    text_color = t["bubble_assistant_text"]
    return f"""
    <style>
    :root, .stApp {{
        --background-color: {t['app_bg']};
        --secondary-background-color: {t['widget_bg']};
        --text-color: {text_color};
    }}
    [data-testid="stAppViewContainer"] {{
        background-color: {t['app_bg']} !important;
        background-image:
            linear-gradient(
                90deg,
                {t['app_bg']} 0%,
                rgba(13,15,20,0.94) 40%,
                rgba(13,15,20,0.6) 60%,
                rgba(13,15,20,0.35) 78%,
                rgba(13,15,20,0.35) 100%
            ),
            url("data:image/jpeg;base64,{hero_bg_b64}");
        background-size: auto, contain;
        background-position: right bottom, right bottom;
        background-repeat: no-repeat, no-repeat;
        background-attachment: fixed, fixed;
    }}
    .block-container {{
        background: transparent !important;
    }}
    [data-testid="stChatInput"] button {{
        background-color: #EEAB59 !important;
        border-radius: 50% !important;
    }}
    [data-testid="stChatInput"] button svg {{
        fill: #412402 !important;
        color: #412402 !important;
    }}
    [data-testid="stSidebar"], [data-testid="stSidebarContent"] {{
        background-color: {t['sidebar_bg']} !important;
        background-image: radial-gradient(circle at 15% 8%, rgba(238,171,89,0.10), transparent 40%);
    }}
    [data-testid="stSidebar"] *, [data-testid="stSidebarContent"] * {{
        color: #F1EFE8 !important;
    }}
    [data-testid="stBottom"], [data-testid="stBottomBlockContainer"] {{
        background-color: {t['app_bg']} !important;
    }}
    [data-testid="stChatInput"] {{
        background: {t['input_bg']} !important;
        border: 0.5px solid {t['input_border']} !important;
        border-radius: 24px !important;
    }}
    [data-testid="stChatInput"] textarea {{
        color: {t['bubble_assistant_text']} !important;
    }}
    [data-testid="stExpander"], [data-baseweb="select"] > div, [data-testid="stTextInput"] input {{
        background-color: {t['widget_bg']} !important;
        color: {text_color} !important;
    }}
    button[kind="secondary"] {{
        background-color: {t['widget_bg']} !important;
        color: {text_color} !important;
    }}
    .chat-bubble {{
        border-radius: 16px;
        padding: 14px 18px;
        font-size: 15.5px;
        line-height: 1.5;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 0.5px solid transparent;
        box-shadow: 0 4px 18px rgba(0,0,0,0.28);
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
        box-shadow: none;
    }}
    .chat-timestamp {{
        display: block;
        font-size: 10.5px;
        color: {t['timestamp_color']};
        margin-top: 4px;
    }}
    .chat-timestamp-user {{
        text-align: right;
    }}
    .sidebar-logo-row {{
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 4px;
    }}
    .sidebar-logo-mark {{
        width: 30px;
        height: 30px;
        border-radius: 8px;
        background: #EEAB59;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        flex-shrink: 0;
    }}
    .sidebar-logo-text {{
        font-family: 'Baloo 2', sans-serif;
        font-weight: 700;
        font-size: 17px;
        line-height: 1.05;
    }}
    .sidebar-logo-text .gold {{ color: #EEAB59; }}
    .sidebar-logo-sub {{
        font-size: 9.5px;
        letter-spacing: 0.06em;
        color: rgba(241, 239, 232, 0.5);
        margin: 0 0 10px 38px;
    }}
    .source-chip {{
        display: inline-block;
        margin-top: 8px;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 11.5px;
        background: {t['chip_bg']};
        color: {t['chip_text']};
        border: 0.5px solid {t['chip_border']};
    }}
    @keyframes rk-typing-bounce {{
        0%, 60%, 100% {{ transform: translateY(0); }}
        30% {{ transform: translateY(-4px); }}
    }}
    .typing-dot {{
        width: 6px;
        height: 6px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 4px;
        opacity: 0.65;
        background: {t['bubble_assistant_text']};
        animation: rk-typing-bounce 1s infinite ease-in-out;
    }}
    .typing-dot:nth-child(2) {{ animation-delay: 0.15s; }}
    .typing-dot:nth-child(3) {{ animation-delay: 0.3s; margin-right: 0; }}
    .feedback-chip {{
        display: inline-block;
        margin-top: 6px;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        background: rgba(80, 160, 60, 0.15);
        color: #8FD65C;
        border: 0.5px solid rgba(80, 160, 60, 0.3);
    }}
    </style>
    """


# Detecta el nombre de archivo .pdf citado dentro de la respuesta del
# agente (ej. "segun Politica_Warranty_Dummy.pdf, pagina 4") para
# mostrarlo como chip visual separado, ademas del texto de la
# respuesta. No se modifica ni se elimina el texto original citado por
# el agente (Cohere no siempre lo frasea igual); esto es puramente
# aditivo para no arriesgar romper la gramatica de la respuesta.
SOURCE_FILENAME_PATTERN = re.compile(
    r"([\wÁÉÍÓÚáéíóúñÑ_\-]+\.pdf)(?:\s*,?\s*(?:p[aá]gina|p\.)\s*(\d+))?",
    re.IGNORECASE,
)


def extract_source_chip_label(text: str) -> str | None:
    """Devuelve la etiqueta del chip de fuente (documento + pagina si se detecto), o None."""
    match = SOURCE_FILENAME_PATTERN.search(text)
    if not match:
        return None
    filename, page = match.group(1), match.group(2)
    label = filename.replace("_Dummy", "").replace("_", " ").replace(".pdf", "").replace(".PDF", "")
    return f"📄 {label} · página {page}" if page else f"📄 {label}"

# Puente de compatibilidad: en Streamlit Community Cloud, las API keys
# se configuran en "Secrets" (st.secrets), no en un archivo .env local.
# Si la key no esta ya en las variables de entorno, la tomamos de
# st.secrets y la exponemos como variable de entorno, para que
# agent.py (que usa os.getenv) funcione igual en ambos entornos.
if "COHERE_API_KEY" not in os.environ and "COHERE_API_KEY" in st.secrets:
    os.environ["COHERE_API_KEY"] = st.secrets["COHERE_API_KEY"]

# Clave de acceso administrador (v2.0): protege la descarga del log de
# feedback, que antes era visible para cualquier persona que abriera
# el sidebar. Mismo patron de compatibilidad que COHERE_API_KEY: en
# Streamlit Cloud se configura en Secrets; en local, en .env.
if "ADMIN_PASSWORD" not in os.environ and "ADMIN_PASSWORD" in st.secrets:
    os.environ["ADMIN_PASSWORD"] = st.secrets["ADMIN_PASSWORD"]
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# Persistencia de feedback via GitHub (v2.0 — alternativa a Supabase,
# sin agregar una base de datos nueva al stack). El filesystem de
# Streamlit Community Cloud es efimero: feedback.jsonl se pierde en
# cada redeploy. En vez de eso, cada feedback se sincroniza tambien
# como commit en una rama DEDICADA del propio repo (no en main ni en
# v2-ui-glassmorphism), para no ensuciar el historial de codigo con
# commits automaticos de feedback. Si GITHUB_TOKEN no esta configurado
# (ej. desarrollo local), la sincronizacion se omite silenciosamente y
# solo se guarda localmente, como antes.
if "GITHUB_TOKEN" not in os.environ and "GITHUB_TOKEN" in st.secrets:
    os.environ["GITHUB_TOKEN"] = st.secrets["GITHUB_TOKEN"]
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = "silvet005-cpu/rlka"
GITHUB_FEEDBACK_BRANCH = "feedback-data"
GITHUB_FEEDBACK_PATH = "docs/feedback.jsonl"

from ingest import load_and_chunk_documents
from vectorstore import build_vectorstore
from agent import answer_question, SALUDO_INICIAL_POR_IDIOMA

FEEDBACK_LOG_PATH = "feedback.jsonl"

st.set_page_config(page_title="RoofKA — RLKA", page_icon="🐆")

if "lang" not in st.session_state:
    st.session_state.lang = "es"


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


def _sync_feedback_to_github(entry: dict) -> None:
    """
    Agrega una linea al feedback.jsonl versionado en GitHub (rama
    dedicada GITHUB_FEEDBACK_BRANCH), para que sobreviva a los
    redeploys de Streamlit Cloud. Falla en silencio (solo advierte en
    consola) si algo sale mal -- nunca debe romper el flujo de dar
    feedback en la UI por un problema de red o de la API de GitHub.
    """
    if not GITHUB_TOKEN:
        return

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    api_base = f"https://api.github.com/repos/{GITHUB_REPO}"
    contents_url = f"{api_base}/contents/{GITHUB_FEEDBACK_PATH}"

    try:
        # 1. Asegurar que la rama dedicada existe; si no, crearla a
        # partir del HEAD actual de main.
        branch_check = requests.get(f"{api_base}/branches/{GITHUB_FEEDBACK_BRANCH}", headers=headers, timeout=10)
        if branch_check.status_code == 404:
            main_ref = requests.get(f"{api_base}/git/ref/heads/main", headers=headers, timeout=10).json()
            main_sha = main_ref["object"]["sha"]
            requests.post(
                f"{api_base}/git/refs",
                headers=headers,
                json={"ref": f"refs/heads/{GITHUB_FEEDBACK_BRANCH}", "sha": main_sha},
                timeout=10,
            )

        # 2. Leer el contenido y sha actuales del archivo en esa rama
        # (si no existe todavia el archivo ahi, se crea desde cero).
        get_resp = requests.get(contents_url, headers=headers, params={"ref": GITHUB_FEEDBACK_BRANCH}, timeout=10)
        if get_resp.status_code == 200:
            data = get_resp.json()
            contenido_actual = base64.b64decode(data["content"]).decode("utf-8")
            sha_actual = data["sha"]
        else:
            contenido_actual = ""
            sha_actual = None

        nuevo_contenido = contenido_actual + json.dumps(entry, ensure_ascii=False) + "\n"
        payload = {
            "message": "chore(feedback): agregar registro de feedback",
            "content": base64.b64encode(nuevo_contenido.encode("utf-8")).decode("utf-8"),
            "branch": GITHUB_FEEDBACK_BRANCH,
        }
        if sha_actual:
            payload["sha"] = sha_actual

        requests.put(contents_url, headers=headers, json=payload, timeout=10)
    except Exception as e:
        print(f"[RoofKA] No se pudo sincronizar feedback a GitHub: {e}")


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
    _sync_feedback_to_github(entry)


index, metadata = get_vectorstore()

AVATAR_ROOFKA = "docs/roofka_avatar_face.png"
AVATAR_USUARIO = "docs/user_avatar_dot.png"

# La CONSULTA real que se envia al agente se mantiene siempre en
# espanol (indices alineados con las 3 preguntas), ya que los
# documentos fuente estan en espanol y esa es la consulta ya validada
# en pruebas reales. Solo el TEXTO MOSTRADO en el boton se traduce por
# idioma -- ver PREGUNTAS_FRECUENTES_DISPLAY mas abajo.
PREGUNTAS_FRECUENTES_ES = [
    "¿Cuánto dura la garantía de un techo completo?",
    "¿Qué incluye el checklist de cierre de instalación?",
    "¿Cómo se clasifica un contratista independiente?",
]

PREGUNTAS_FRECUENTES_DISPLAY = {
    "es": PREGUNTAS_FRECUENTES_ES,
    "en": [
        "How long does a full roof warranty last?",
        "What does the installation closeout checklist include?",
        "How is an independent contractor classified?",
    ],
    "pt": [
        "Quanto tempo dura a garantia de um telhado completo?",
        "O que inclui o checklist de encerramento da instalação?",
        "Como um contratado independente é classificado?",
    ],
}

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;700&family=Inter:wght@400;500;600&family=Poppins:wght@700;800;900&display=swap');

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

with open("docs/roofka_hero_bg.jpg", "rb") as f:
    _hero_bg_b64 = base64.b64encode(f.read()).decode()

st.markdown(get_theme_css(_hero_bg_b64), unsafe_allow_html=True)

lang = st.session_state.lang
txt = TEXTS[lang]

st.markdown(
    f"""
    <div style="display:inline-block; margin-bottom:8px;">
        <span style="
            display:inline-flex;
            align-items:center;
            gap:10px;
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            background: rgba(13,15,20,0.45);
            padding: 8px 18px;
            border-radius: 14px;
        ">
            <span style="color:#FFFFFF; font-size:34px; line-height:1;
                font-family:'Poppins', sans-serif; font-weight:800; letter-spacing:-0.01em;">
                RoofKA
            </span>
            <span style="background:#EEAB59; color:#412402; font-size:13px; font-weight:800;
                font-family:'Poppins', sans-serif; padding:3px 11px; border-radius:10px;">
                IA
            </span>
        </span>
    </div>
    <p style="margin:2px 0 0; font-size:14.5px; color:#D3D1C7; max-width:480px; line-height:1.45;
        text-shadow: 0 1px 6px rgba(0,0,0,0.6);">
        {txt['header_caption']}
    </p>
    """,
    unsafe_allow_html=True,
)

# Reserva de espacio a la derecha para que el texto del chat no se
# superponga visualmente con el personaje (la foto de fondo ya se
# aplico completa en get_theme_css(), sobre stAppViewContainer). La
# frase que antes flotaba sobre la foto se elimino (se superponia de
# forma que "ensuciaba" la imagen); ese mensaje ahora vive combinado
# con la leyenda del panel izquierdo (ver docs_caption en TEXTS).
st.markdown(
    """
    <style>
    .block-container {
        padding-right: 340px !important;
    }
    @media (max-width: 1000px) {
        .block-container { padding-right: 1.5rem !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with open("docs/roofka_sidebar_logo.png", "rb") as f:
    _sidebar_logo_b64 = base64.b64encode(f.read()).decode()

with st.sidebar:
    st.markdown(
        f"""
        <img src="data:image/png;base64,{_sidebar_logo_b64}"
             style="width:100%; max-width:220px; display:block; margin-bottom:12px;" />
        """,
        unsafe_allow_html=True,
    )

    _col_es, _col_en, _col_pt = st.columns(3)
    with _col_es:
        if st.button("ES", use_container_width=True, type="primary" if lang == "es" else "secondary"):
            st.session_state.lang = "es"
            st.rerun()
    with _col_en:
        if st.button("EN", use_container_width=True, type="primary" if lang == "en" else "secondary"):
            st.session_state.lang = "en"
            st.rerun()
    with _col_pt:
        if st.button("PT", use_container_width=True, type="primary" if lang == "pt" else "secondary"):
            st.session_state.lang = "pt"
            st.rerun()

    st.subheader(txt["docs_header"])
    st.markdown(txt["docs_list"])
    st.caption(txt["docs_caption"])

    st.divider()
    st.subheader(txt["faq_header"])
    if lang != "es":
        st.caption(txt["faq_note"])
    pregunta_frecuente = None
    for idx, pregunta_faq_es in enumerate(PREGUNTAS_FRECUENTES_ES):
        etiqueta_mostrada = PREGUNTAS_FRECUENTES_DISPLAY[lang][idx]
        if st.button(
            etiqueta_mostrada,
            use_container_width=True,
            type="primary",
            disabled=st.session_state.get("procesando", False),
        ):
            # Tupla (texto mostrado en la burbuja, texto real enviado
            # al agente para la busqueda). Se mantienen separados: el
            # texto de busqueda siempre va en espanol -- es la consulta
            # ya validada contra los documentos --, mientras que la
            # burbuja del usuario muestra el idioma que el usuario
            # realmente clickeo, para que no se vea inconsistente.
            pregunta_frecuente = (etiqueta_mostrada, pregunta_faq_es)

    st.divider()

    # Tip y Registro de ejecucion van agrupados aqui, DESPUES de las
    # preguntas frecuentes: son herramientas secundarias/auxiliares, no
    # el flujo principal de uso, asi que se colocan al final para no
    # competir visualmente con los botones de FAQ (que usan
    # type="primary" y deben ganar la atencion primero). Ambos usan el
    # mismo emoji de referencia a la marca (leopardo) para verse
    # consistentes entre si.
    with st.expander(txt["tip_header"]):
        st.caption(txt["tip_body"])

    # Descarga del log de ejecucion (tarjeta 8 - registrar ejecucion).
    # Agrupado en un expander, colapsado por defecto: es una herramienta
    # de auditoria/evidencia, no parte del flujo de uso normal del
    # agente, asi que no debe competir visualmente con las preguntas
    # frecuentes. El filesystem de Streamlit Community Cloud es efimero
    # (feedback.jsonl se pierde en cada redeploy), de ahi la necesidad
    # de poder bajarlo como evidencia antes de que eso pase.
    with st.expander(txt["log_header"]):
        st.caption(txt["log_caption"])
        if "admin_autenticado" not in st.session_state:
            st.session_state.admin_autenticado = False

        if st.session_state.admin_autenticado:
            if os.path.exists(FEEDBACK_LOG_PATH):
                with open(FEEDBACK_LOG_PATH, "rb") as f:
                    st.download_button(
                        txt["download_btn"],
                        data=f,
                        file_name="feedback.jsonl",
                        mime="application/jsonl",
                        use_container_width=True,
                    )
            else:
                st.caption(txt["log_empty"])
        elif not ADMIN_PASSWORD:
            # Si no se configuro ninguna clave (entorno local sin
            # secrets), no bloqueamos por accidente el flujo de trabajo
            # de quien esta desarrollando la app.
            st.caption(txt["admin_unset_warning"])
            if os.path.exists(FEEDBACK_LOG_PATH):
                with open(FEEDBACK_LOG_PATH, "rb") as f:
                    st.download_button(
                        txt["download_btn"],
                        data=f,
                        file_name="feedback.jsonl",
                        mime="application/jsonl",
                        use_container_width=True,
                    )
        else:
            st.caption(txt["admin_locked_caption"])
            clave_ingresada = st.text_input(
                txt["admin_password_label"], type="password", key="admin_password_input"
            )
            if st.button(txt["admin_verify_btn"], use_container_width=True):
                if clave_ingresada == ADMIN_PASSWORD:
                    st.session_state.admin_autenticado = True
                    st.rerun()
                else:
                    st.error(txt["admin_wrong_password"])

if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": SALUDO_INICIAL_POR_IDIOMA[lang],
        "time": datetime.now().strftime("%I:%M %p"),
    }]
elif len(st.session_state.messages) == 1:
    # Mientras la conversacion no haya empezado (solo esta el saludo),
    # lo actualizamos al idioma actual cada vez -- si no, cambiar el
    # selector de idioma no se reflejaba en el saludo ya guardado desde
    # el arranque de la sesion. Una vez hay conversacion real, no se
    # retraduce el historial (ver TEXTS/agent.py: no se retraducen
    # respuestas ya generadas).
    st.session_state.messages[0]["content"] = SALUDO_INICIAL_POR_IDIOMA[lang]
if "feedback_dado" not in st.session_state:
    st.session_state.feedback_dado = True  # no hay respuesta nueva pendiente de calificar
if "procesando" not in st.session_state:
    st.session_state.procesando = False  # True mientras se espera la respuesta del agente
if "pregunta_pendiente" not in st.session_state:
    st.session_state.pregunta_pendiente = None
if "feedback_por_indice" not in st.session_state:
    st.session_state.feedback_por_indice = {}  # {indice_mensaje: "positivo"/"negativo"}

# NOTA: la tarjeta de "contacto" (RoofKA + badge IA + subtitulo) que
# antes vivia aqui arriba de la conversacion se elimino -- es
# redundante ahora que el mismo tratamiento (nombre + badge IA) se
# aplico directamente al titulo principal de la pagina.

for i, msg in enumerate(st.session_state.messages):
    avatar = AVATAR_ROOFKA if msg["role"] == "assistant" else AVATAR_USUARIO
    bubble_class = "chat-bubble-assistant" if msg["role"] == "assistant" else "chat-bubble-user"
    timestamp_class = "chat-timestamp" if msg["role"] == "assistant" else "chat-timestamp chat-timestamp-user"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(
            f"<div class='chat-bubble {bubble_class}'>{_markdown_bold_to_html(msg['content'])}</div>"
            f"<span class='{timestamp_class}'>{msg.get('time', '')}</span>",
            unsafe_allow_html=True,
        )
        if msg["role"] == "assistant":
            chip_label = extract_source_chip_label(msg["content"])
            if chip_label:
                st.markdown(f"<span class='source-chip'>{chip_label}</span>", unsafe_allow_html=True)

        # Botones de feedback (tarjeta 8 - registrar ejecucion).
        # Se colocan aqui, ligados a session_state, y NO dentro del
        # bloque "if pregunta:" de mas abajo: st.chat_input() solo
        # devuelve texto en la ejecucion donde se escribio, asi que en
        # la ejecucion disparada por el clic en 👍/👎 "pregunta" ya
        # vuelve a estar vacio y ese bloque completo se saltaria,
        # perdiendo el clic antes de llamar a log_feedback(). Al usar
        # una bandera en session_state, el boton se sigue mostrando
        # (y el clic si se procesa) en la ejecucion siguiente.
        if i in st.session_state.feedback_por_indice:
            # Confirmacion visual persistente (no solo el toast, que
            # desaparece rapido): el usuario puede ver, incluso
            # revisando el historial despues, que su feedback quedo
            # registrado.
            st.markdown(
                f"<span class='feedback-chip'>{txt['feedback_chip']}</span>",
                unsafe_allow_html=True,
            )
        else:
            es_ultimo_mensaje = i == len(st.session_state.messages) - 1
            if msg["role"] == "assistant" and es_ultimo_mensaje and not st.session_state.feedback_dado:
                st.markdown("<div style='margin-top:6px;'></div>", unsafe_allow_html=True)
                col1, col2, _ = st.columns([0.1, 0.1, 0.8])
                with col1:
                    if st.button("👍", key=f"like_{i}", type="primary"):
                        log_feedback(st.session_state.messages[i - 1]["content"], msg["content"], "positivo")
                        st.session_state.feedback_por_indice[i] = "positivo"
                        st.session_state.feedback_dado = True
                        st.toast(txt["toast_positivo"])
                        st.rerun()
                with col2:
                    if st.button("👎", key=f"dislike_{i}"):
                        log_feedback(st.session_state.messages[i - 1]["content"], msg["content"], "negativo")
                        st.session_state.feedback_por_indice[i] = "negativo"
                        st.session_state.feedback_dado = True
                        st.toast(txt["toast_negativo"])
                        st.rerun()

if len(st.session_state.messages) == 1 and not st.session_state.procesando:
    st.caption(txt["empty_state_caption"])

# Fase 1 — Envio: se limita a anotar la pregunta y bloquear la UI de
# inmediato (sin llamar todavia a answer_question, que es lo lento).
# Bloqueamos ANTES de procesar para que los botones/input ya se vean
# deshabilitados durante toda la espera de Cohere, no solo al final.
# Esto es lo que evita que una segunda pregunta se dispare mientras la
# primera sigue en curso (ver docs/Log_Cambios_RLKA.md).
texto_tipeado = st.chat_input(
    txt["chat_placeholder"],
    disabled=st.session_state.procesando,
)
# Normalizamos ambas fuentes a la misma forma (texto_mostrado, texto_busqueda):
# lo tipeado a mano usa el mismo texto para ambos; las preguntas
# frecuentes ya vienen como esa tupla desde el sidebar.
if texto_tipeado:
    pregunta_nueva = (texto_tipeado, texto_tipeado)
else:
    pregunta_nueva = pregunta_frecuente

if pregunta_nueva and not st.session_state.procesando:
    texto_mostrado, texto_busqueda = pregunta_nueva
    st.session_state.messages.append({
        "role": "user",
        "content": texto_mostrado,
        "time": datetime.now().strftime("%I:%M %p"),
    })
    st.session_state.procesando = True
    st.session_state.pregunta_pendiente = texto_busqueda
    st.rerun()

# Fase 2 — Procesamiento: corre en la ejecucion siguiente, con la UI ya
# bloqueada (botones e input deshabilitados) mientras se espera Cohere.
if st.session_state.procesando:
    with st.chat_message("assistant", avatar=AVATAR_ROOFKA):
        typing_placeholder = st.empty()
        typing_placeholder.markdown(
            "<div class='chat-bubble chat-bubble-assistant'>"
            "<span class='typing-dot'></span>"
            "<span class='typing-dot'></span>"
            "<span class='typing-dot'></span>"
            "</div>",
            unsafe_allow_html=True,
        )
        respuesta = answer_question(st.session_state.pregunta_pendiente, index, metadata, lang=lang)
        _hora_respuesta = datetime.now().strftime("%I:%M %p")
        typing_placeholder.empty()
        st.markdown(
            f"<div class='chat-bubble chat-bubble-assistant'>{_markdown_bold_to_html(respuesta)}</div>"
            f"<span class='chat-timestamp'>{_hora_respuesta}</span>",
            unsafe_allow_html=True,
        )
        chip_label = extract_source_chip_label(respuesta)
        if chip_label:
            st.markdown(f"<span class='source-chip'>{chip_label}</span>", unsafe_allow_html=True)

    st.session_state.messages.append({
        "role": "assistant",
        "content": respuesta,
        "time": _hora_respuesta,
    })
    st.session_state.feedback_dado = False  # respuesta nueva, aun sin calificar
    st.session_state.procesando = False
    st.session_state.pregunta_pendiente = None
    st.rerun()  # fuerza una ejecucion limpia: UI desbloqueada + botones de feedback consistentes

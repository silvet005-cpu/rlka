# Log de Cambios — RLKA (Roof Leopard Knowledge Agent)

Registro cronológico de correcciones y hallazgos técnicos relevantes durante el desarrollo, complementario a los ADR (que registran decisiones de arquitectura) y al historial de commits de GitHub (que registra el detalle técnico de cada cambio). Sirve como evidencia de auditoría y mejora continua (tarjeta 8 — Registrar ejecución del proyecto).

---

## 2026-07-08 — Compatibilidad de dependencias en Streamlit Community Cloud

**Contexto:** al desplegar `app.py` en Streamlit Community Cloud, el build falló.

**Hallazgo:** Streamlit Community Cloud provisiona el entorno con Python 3.14. La versión fijada de `streamlit==1.38.0` dependía de `pillow==10.4.0`, una versión sin paquete pre-compilado ("wheel") para Python 3.14. El sistema intentó compilar Pillow desde el código fuente y falló por falta de la librería `zlib` en el entorno.

**Corrección:**
- `streamlit` actualizado de `1.38.0` → `1.59.1`
- `numpy` actualizado de `2.0.2` → `2.5.1`

(ambas versiones sí cuentan con paquetes pre-compilados para Python 3.14, evitando la compilación desde fuente)

**Archivo afectado:** `requirements.txt`
**Commit:** `fix: streamlit y numpy compatibles`

**Adicional:** se agregó `packages.txt` (con `poppler-utils`) en la raíz del repositorio, ya que Streamlit Community Cloud no lo trae preinstalado y `ingest.py` depende de `pdftotext` para la extracción de texto.

---

## 2026-07-09 — Botones de feedback (👍/👎) no registraban los clics

**Contexto:** al agregar un botón de descarga de `feedback.jsonl` en el sidebar (para tener evidencia de ejecución descargable), se detectó que el archivo nunca se creaba en el servidor, sin importar cuántas veces se le diera clic a 👍 o 👎.

**Hallazgo:** los botones de feedback estaban definidos dentro del bloque `if pregunta:`, condicionado al valor devuelto por `st.chat_input()`. Streamlit reejecuta todo el script en cada interacción, y `chat_input()` solo devuelve el texto de la pregunta en la ejecución donde se escribió — en la ejecución disparada por el clic en 👍/👎, `pregunta` ya es `None`, así que ese bloque completo (incluyendo los botones) nunca se ejecutaba, y el clic se perdía antes de llamar a `log_feedback()`.

**Corrección:** se movieron los botones fuera de `if pregunta:`, hacia el bucle que dibuja el historial de mensajes, controlados por una bandera independiente en `st.session_state` (`feedback_dado`). Esto asegura que el botón se siga mostrando (y el clic sí se procese) en la ejecución siguiente, sin depender del input efímero.

**Archivo afectado:** `src/app.py`
**Commit:** `fix: boton de feedback no registraba clics (session_state en vez de chat_input)`

**Validación:** confirmado en producción — 5 preguntas de prueba quedaron registradas correctamente en `feedback.jsonl` con `timestamp`, `question`, `answer` y `feedback` (ver `docs/feedback.jsonl`).

---

## 2026-07-09 — Limitación de retrieval en preguntas que cruzan dos temas en un solo enunciado

**Contexto:** durante las pruebas de feedback en producción, se envió la pregunta "Clasificación de contratista y garantía de un techo?".

**Hallazgo:** el agente respondió correctamente la parte de garantía (citando `Politica_Warranty_Dummy.pdf`), pero indicó no tener información sobre la clasificación de contratista — aunque esa información sí existe en `Politica_RRHH_Dummy.pdf, página 2`, y el agente la había citado correctamente antes cuando se preguntó por separado. Esto sugiere que cuando una sola oración combina dos temas de documentos distintos, el retrieval no siempre trae los chunks relevantes de ambos.

**Estado:** pendiente de corrección. Documentado como mejora futura en `Mejoras_Futuras_RLKA.md` (ajustar `top_k` o dividir la consulta en sub-preguntas antes del retrieval cuando se detecten múltiples temas en un solo enunciado).

---

## 2026-07-09 — Aclaración oficial: OCI no es obligatorio para el deploy

**Contexto:** la tarjeta 7 del tablero de Trello indicaba textualmente "es obligatorio usar al menos un servicio del ecosistema de OCI en este proceso de despliegue". Antes de invertir tiempo en una integración con Object Storage, se consultó directamente al canal de soporte oficial del programa (OneSource) para confirmar el alcance real del requisito.

**Respuesta oficial (OneSource, Slack del programa):** "No es obligatorio usar Oracle Cloud Infrastructure (OCI) para el Challenge. Puedes realizar el deploy en la plataforma que prefieras, siempre que tu proyecto sea accesible mediante una URL pública. OCI es solo una recomendación del programa."

**Decisión:** no se integra ningún servicio de OCI. El despliegue permanece en Streamlit Community Cloud (`rlka-roofka.streamlit.app`), que ya cumple el requisito real (accesibilidad vía URL pública), evitando agregar una dependencia de red innecesaria a un despliegue ya estable y validado.

**Archivos afectados:** `README.md` (sección "Tecnologias" corregida para reflejar Streamlit Community Cloud como plataforma de despliegue, en vez de OCI).
**Tarjeta de Trello:** 7 — cerrada tal como está, sin cambios adicionales de infraestructura.

---

*Este documento se actualiza conforme surgen nuevos hallazgos relevantes durante el desarrollo y las pruebas en producción.*

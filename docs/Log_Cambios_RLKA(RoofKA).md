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

**Respuesta oficial (OneSource, Discord del programa):** "No es obligatorio usar Oracle Cloud Infrastructure (OCI) para el Challenge. Puedes realizar el deploy en la plataforma que prefieras, siempre que tu proyecto sea accesible mediante una URL pública. OCI es solo una recomendación del programa."

**Decisión:** no se integra ningún servicio de OCI. El despliegue permanece en Streamlit Community Cloud (`rlka-roofka.streamlit.app`), que ya cumple el requisito real (accesibilidad vía URL pública), evitando agregar una dependencia de red innecesaria a un despliegue ya estable y validado.

**Archivos afectados:** `README.md` (sección "Tecnologias" corregida para reflejar Streamlit Community Cloud como plataforma de despliegue, en vez de OCI).
**Tarjeta de Trello:** 7 — cerrada tal como está, sin cambios adicionales de infraestructura.

---

## 2026-07-10 — Retrieval fallaba en preguntas de una sola palabra técnica ("nómina", "closeout")

**Contexto:** durante pruebas de la categoría 6 del log de variaciones (preguntas cortas), "contratista" respondía correctamente, pero "nómina" y "closeout" activaban el fallback ("no tengo esa información") aunque el contenido sí existe en `Politica_RRHH_Dummy.pdf` y `Manual_Procedimientos_Operativos_Dummy.pdf` respectivamente. Se confirmó que no era un problema de typo probando también con "claseout".

**Hallazgo:** el fix anterior de preguntas cortas (ampliar `top_k` a 8) no ataca la causa raíz. El umbral de confianza (`SIMILARITY_THRESHOLD = 0.45`) se evalúa sobre el mejor resultado de la búsqueda, y ese resultado nunca llega a superarlo para ciertas palabras sueltas — el modelo de embeddings (`paraphrase-multilingual-MiniLM-L12-v2`) está entrenado para comparar el significado de oraciones completas, no palabras aisladas. "Contratista" pasaba por aparecer en contextos ricos dentro de RRHH; "nómina" y "closeout" no generaban suficiente señal semántica como palabra suelta. Se confirmó manualmente que expandir la consulta a "información sobre nómina" sí recupera el contenido correcto.

**Corrección:** se agregó la función `construir_consulta_busqueda()` en `agent.py`, que expande el TEXTO usado únicamente para el embedding de búsqueda cuando la pregunta tiene ≤3 palabras (prefijo "información sobre"), sin modificar la pregunta original que ve el usuario, el prompt de Cohere, ni el umbral de confianza — evitando debilitar la protección contra alucinaciones.

**Archivo afectado:** `src/agent.py`
**Commit:** `fix: mejorar retrieval de consultas cortas`

**Nota sobre el proceso de validación:** la primera prueba en producción tras el commit pareció indicar que el fix no funcionaba ("nómina" seguía en fallback). Se descartó revertir el código sin evidencia y, en su lugar, se agregó temporalmente una línea de debug (`commit: debug: mostrar consulta de búsqueda real`) que mostraba en pantalla la consulta real usada para la búsqueda. Esto permitió confirmar que el problema era un retraso del redeploy automático de Streamlit Community Cloud, no un error de lógica. Tras el redeploy, "nómina" y "closeout" respondieron correctamente con Cohere en producción. La línea de debug se removió (`commit: chore: quitar debug temporal de consulta de búsqueda, fix confirmado en producción`) una vez confirmado.

**Validación:** confirmado en producción para los 3 casos de la categoría 6 (`contratista`, `nómina`, `closeout`) — ver `docs/Log_Pruebas_Preguntas_RLKA.md`.

**Relacionado:** también se movió el bloque "💡 Tip: cómo preguntar mejor" del área de chat al sidebar, agrupado junto a "Registro de ejecución" (`commit: refactor: mover Tip al sidebar`), para que quede accesible de forma persistente durante toda la sesión sin competir visualmente con los botones de "Preguntas frecuentes".

---

*Este documento se actualiza conforme surgen nuevos hallazgos relevantes durante el desarrollo y las pruebas en producción.*

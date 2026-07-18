# Mejoras Futuras — RLKA (Roof Leopard Knowledge Agent)

Este documento reúne ideas identificadas durante el desarrollo que **no son parte del alcance obligatorio** de la entrega evaluada del challenge (v1.0, en `main`), organizadas por fase.

---

## Fase 2 (v2.0 — rama `v2-ui-glassmorphism`) — ya resuelto

### 1. Persistencia del feedback (👍/👎)

**Estado: ✅ implementado.** `app.py` sigue escribiendo `feedback.jsonl` localmente, pero además cada feedback se sincroniza vía la API de GitHub como commit en una rama dedicada (`feedback-data`, separada de `main` y de `v2-ui-glassmorphism` para no ensuciar el historial de código). Se descartó Supabase para no agregar una base de datos externa al stack, aprovechando el propio repositorio como almacenamiento persistente.

**Configuración requerida:** variable `GITHUB_TOKEN` (Fine-grained PAT limitado solo a este repo, permiso "Contents: Read and write"). Sin esa variable, cae de vuelta al comportamiento anterior (solo local) sin romper la app.

---

## Fase 3 (pendiente, sin empezar) — ideas evaluadas y descartadas por ahora

### 2. Cuarto botón de "Pregunta frecuente" — razonamiento cruzado

**Situación actual:** el sidebar tiene 3 botones de preguntas frecuentes, cada uno enfocado en un solo documento/tema.

**Idea evaluada, sin decidir aún:** agregar un 4to botón que muestre una pregunta que cruce información entre 2 documentos (por ejemplo, Manual de Procedimientos + Warranty ante un daño estructural con Change Order), como vitrina del razonamiento cruzado que ya sabemos que RoofKA hace bien (confirmado en el log de pruebas, categoría 4).

**Pendiente:** decidir si vale la pena por el valor de mostrar esta capacidad, versus el riesgo de sobrecargar el sidebar con demasiados botones.

### 3. Personalización por persona (saludo por nombre, avatar por rol)

**Idea evaluada, explícitamente pospuesta durante la v2.0:** que RoofKA salude por nombre y ajuste el avatar según quién esté usando la app (Willie, Rob, James, Matt, Daniel, Silvia).

**Nivel de esfuerzo, según se decida:**
- *Selector simple* (sin contraseña): un dropdown "¿Quién eres?" al inicio, guardado en sesión — personalización, no autenticación real.
- *Login real* con contraseña por persona — bastante más trabajo, cambia el alcance del proyecto.

**Pendiente:** decidir cuál de las dos rutas (o ninguna, por ahora).

### 4. Pulido visual adicional (nivel diseño UI, bajo riesgo)

Ideas señaladas durante la revisión visual de la v2.0, no implementadas aún:
- Estados de hover/focus visibles en los botones de FAQ (accesibilidad de teclado incluida).
- Escala de radio de bordes consistente en todos los componentes (actualmente varía entre 12/14/16/20px según el elemento).
- Auditoría de contraste real (no solo visual) del texto sobre la foto de fondo, con una herramienta dedicada.
- Transición suave (fade) al cambiar de idioma, en vez de refresco instantáneo.

### 5. Decisión de merge a `main`

La v2.0 vive en la rama `v2-ui-glassmorphism`, desplegada por separado en `rlka-roofka-v2.streamlit.app`. Pendiente decidir cuándo (o si) fusionarla a `main`, reemplazando la interfaz evaluada por el challenge. Recomendado: esperar un período de uso real antes de fusionar.

---

*Última actualización: cierre de la Fase 2 (v2.0, mejoras de UI/UX) — RLKA.*

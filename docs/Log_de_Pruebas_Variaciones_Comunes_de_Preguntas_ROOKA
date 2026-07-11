# Log de Pruebas — Variaciones Comunes de Preguntas (RLKA)

Registro de casos de prueba para validar que RoofKA responde bien ante distintas formas reales de preguntar, no solo preguntas "perfectas". Cada fila se completa después de probar en la app.

## Cómo usar este log
Prueba cada pregunta en `rlka-roofka.streamlit.app`, anota qué respondió (o pega la captura), y marca si el resultado fue correcto, parcial, o incorrecto.

---

## 1. Sin tildes
| Pregunta | Resultado | Estado |
|---|---|---|
| `cuanto dura la garantia de un techo completo` | Recuperó el mismo contenido correcto que con tildes (Politica_Warranty_Dummy.pdf, página 4), sin perder precisión. | ✅ |
| `que incluye el checklist de cierre` | Respondió correctamente, citando Manual_Procedimientos_Operativos_Dummy.pdf, página 3, incluyendo el detalle del Supervisor de Campo. | ✅ |

## 2. Sin signos de interrogación
| Pregunta | Resultado | Estado |
|---|---|---|
| `cuanto dura la garantia de un techo completo` (sin ¿?) | Cubierta por la misma prueba de la categoría 1 (tampoco llevaba signos de interrogación) — respondió correctamente. | ✅ |

## 3. Errores de escritura (typos)
| Pregunta | Resultado | Estado |
|---|---|---|
| `cuanto dura la garantia de un techo completoo` | Respondió correctamente pese al error de tipeo. | ✅ |
| `komo se clasifica un contratista` | Respondió correctamente pese al error de tipeo. | ✅ |
| `ue incluye el checklist de cierre` (typo de una letra, falta la "q") | Primera ejecución generó salida corrupta (cadena de asteriscos, sin contenido legible); segunda ejecución con el mismo texto exacto respondió correctamente y completo. No reproducible — posible glitch transitorio de la API de Cohere, no bug de código. Sin acción correctiva (no vale la pena perseguir un caso no reproducible). | ⚠️ |

## 4. Preguntas combinadas (2 temas en 1)
| Pregunta | Resultado | Estado |
|---|---|---|
| `cuanto dura la garantia y como se clasifica un contratista` | Respondió ambas partes correctamente, citando Warranty (pág. 3) para la garantía y RRHH (pág. 2) para la clasificación del contratista, sin mezclar el contenido de los dos documentos. | ✅ |
| `que incluye el checklist de cierre y que dice la garantia sobre techos` | Respondió ambas partes correctamente, citando Manual (pág. 3) y Warranty (pág. 6) para el checklist, y Warranty (pág. 4) para la garantía de techos. | ✅ |
| `Clasificación de contratista y garantía de un techo?` (registrado en feedback.jsonl, 2026-07-09) | Respondió correctamente la parte de garantía (Warranty, pág. 4), pero no encontró información sobre la clasificación de contratista, aunque esa información sí existe en Politica_RRHH_Dummy.pdf, página 2. El retrieval no siempre trae los chunks relevantes de ambos documentos cuando los dos temas se combinan en una sola oración. Documentado como mejora futura en `Mejoras_Futuras_RLKA.md`. | ❌ |

## 5. Tono informal / conversacional
| Pregunta | Resultado | Estado |
|---|---|---|
| `oye cuanto me dura la garantia del techo` | Respondió correctamente pese al tono conversacional. | ✅ |
| `hola, quisiera saber sobre el checklist de cierre porfa` | Respondió correctamente pese al tono conversacional. | ✅ |

## 6. Preguntas cortas (ya corregidas — confirmar que ahora sí funcionan)
| Pregunta | Resultado | Estado |
|---|---|---|
| `contratista` | Respondió correctamente desde la primera prueba. | ✅ |
| `nómina` | Primera prueba (antes del fix de expansión de consulta): fallback incorrecto, no encontró contenido que sí existe en Politica_RRHH_Dummy.pdf. Tras aplicar el fix (expandir la consulta a "información sobre nómina" antes del embedding de búsqueda) y confirmar el deploy, respondió correctamente en producción con Cohere. | ✅ |
| `closeout` | Mismo comportamiento que "nómina": falló antes del fix (confirmado también con "claseout" para descartar que fuera un typo), funcionó después del fix, con respuesta completa citando 3 páginas distintas del Manual y Warranty. | ✅ |

**Nota sobre el fix:** ver detalle completo en `Log_Cambios_RLKA(RoofKA).md` — incluye el hallazgo de la causa raíz (embeddings de una sola palabra por debajo del umbral de confianza), la corrección en `agent.py`, y un retraso de deploy en Streamlit Community Cloud que inicialmente hizo parecer que el fix no funcionaba.

## 7. Preguntas fuera de alcance (confirmar que el fallback sigue funcionando)
| Pregunta | Resultado | Estado |
|---|---|---|
| `cual es la capital de francia` | Fallback correcto: "No tengo esa información en los documentos disponibles. Puedo ayudarte con preguntas sobre garantías, procedimientos operativos o políticas de RRHH." No inventó respuesta. | ✅ |
| `cuanto cuesta un iphone` | Mismo fallback correcto, sin inventar respuesta. | ✅ |

---

**Leyenda de Estado:** ✅ Correcto — ⚠️ Parcial/mejorable — ❌ Incorrecto — ⬜ Sin probar

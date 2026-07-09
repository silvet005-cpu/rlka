# Log de Pruebas — Variaciones Comunes de Preguntas (RLKA)

Registro de casos de prueba para validar que RoofKA responde bien ante distintas formas reales de preguntar, no solo preguntas "perfectas". Cada fila se completa después de probar en la app.

## Cómo usar este log
Prueba cada pregunta en `rlka-roofka.streamlit.app`, anota qué respondió (o pega la captura), y marca si el resultado fue correcto, parcial, o incorrecto.

---

## 1. Sin tildes
| Pregunta | Resultado | Estado |
|---|---|---|
| `cuanto dura la garantia de un techo completo` | | ⬜ |
| `que incluye el checklist de cierre` | | ⬜ |

## 2. Sin signos de interrogación
| Pregunta | Resultado | Estado |
|---|---|---|
| `cuanto dura la garantia de un techo completo` (sin ¿?) | | ⬜ |

## 3. Errores de escritura (typos)
| Pregunta | Resultado | Estado |
|---|---|---|
| `cuanto dura la garantia de un techo completoo` | | ⬜ |
| `komo se clasifica un contratista` | | ⬜ |

## 4. Preguntas combinadas (2 temas en 1)
| Pregunta | Resultado | Estado |
|---|---|---|
| `cuanto dura la garantia y como se clasifica un contratista` | Respondió ambas partes correctamente, citando Warranty (pág. 3) para la garantía y RRHH (pág. 2) para la clasificación del contratista, sin mezclar el contenido de los dos documentos. | ✅ |
| `que incluye el checklist de cierre y que dice la garantia sobre techos` | Respondió ambas partes correctamente, citando Manual (pág. 3) y Warranty (pág. 6) para el checklist, y Warranty (pág. 4) para la garantía de techos. | ✅ |

## 5. Tono informal / conversacional
| Pregunta | Resultado | Estado |
|---|---|---|
| `oye cuanto me dura la garantia del techo` | | ⬜ |
| `hola, quisiera saber sobre el checklist de cierre porfa` | | ⬜ |

## 6. Preguntas cortas (ya corregidas — confirmar que ahora sí funcionan)
| Pregunta | Resultado | Estado |
|---|---|---|
| `contratista` | | ⬜ |
| `nómina` | | ⬜ |
| `closeout` | | ⬜ |

## 7. Preguntas fuera de alcance (confirmar que el fallback sigue funcionando)
| Pregunta | Resultado | Estado |
|---|---|---|
| `cual es la capital de francia` | Fallback correcto: "No tengo esa información en los documentos disponibles. Puedo ayudarte con preguntas sobre garantías, procedimientos operativos o políticas de RRHH." No inventó respuesta. | ✅ |
| `cuanto cuesta un iphone` | Mismo fallback correcto, sin inventar respuesta. | ✅ |

---

**Leyenda de Estado:** ✅ Correcto — ⚠️ Parcial/mejorable — ❌ Incorrecto — ⬜ Sin probar

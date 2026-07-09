# Mejoras Futuras — RLKA (Roof Leopard Knowledge Agent)

Este documento reúne ideas identificadas durante el desarrollo del challenge que **no son parte del alcance obligatorio** de la entrega actual (Oracle Tech Builder Challenge), pero que vale la pena evaluar en una segunda fase, una vez cerrado el entregable.

---

## 1. Persistencia del feedback (👍/👎)

**Situación actual:** `app.py` registra el feedback de cada respuesta en `feedback.jsonl`, escrito al sistema de archivos local de Streamlit Community Cloud.

**Limitación:** ese sistema de archivos es efímero — el archivo se pierde cada vez que la app se reinicia o se redespliega (por ejemplo, al hacer push de cambios al repo).

**Mejora propuesta:** migrar el logging de feedback a un almacenamiento persistente, aprovechando que ya se usa Supabase en otro proyecto de Roof Leopard (Marketing Console). Esto permitiría acumular feedback real de los usuarios a lo largo del tiempo sin perderlo en cada deploy.

---

## 2. Cuarto botón de "Pregunta frecuente" — razonamiento cruzado

**Situación actual:** el sidebar de la app tiene 3 botones de preguntas frecuentes, cada uno enfocado en un solo documento/tema.

**Idea evaluada, sin decidir aún:** agregar un 4to botón que muestre una pregunta que cruce información entre 2 documentos (por ejemplo, Manual de Procedimientos + Warranty ante un daño estructural con Change Order), como vitrina del razonamiento cruzado que ya sabemos que RoofKA hace bien (confirmado en el log de pruebas, categoría 4).

**Pendiente:** decidir si vale la pena por el valor de mostrar esta capacidad, versus el riesgo de sobrecargar el sidebar con demasiados botones.

---

*Última actualización: parte del proceso de documentación del Challenge Oracle Tech Builder / Alura ONE — RLKA.*

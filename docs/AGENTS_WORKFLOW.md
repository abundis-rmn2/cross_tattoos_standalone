# 🔄 FLUJO DE TRABAJO DEL AGENTE (PIPELINES ASÍNCRONOS)

Al desarrollar módulos, debes estructurar el procesamiento asumiendo que manejaremos millones de registros a través de colas de mensajería (ej. Celery, RabbitMQ), no mediante ejecución sincrónica.

## FASE 1: Ingesta Resiliente (Adapter Layer)
* **Acción:** Construye adaptadores que lean la fuente estatal, mapeen columnas y envíen registros a una cola.
* **Regla de Fallo:** Implementa una `Dead Letter Queue` (DLQ). Si un registro falla al leerse, se va a la DLQ. NUNCA detengas el ciclo de ingesta.

## FASE 2: Normalización y Extracción Semántica (LLM Layer)
* **Acción:** 1. Toma el texto crudo y envíalo al LLM usando el esquema JSON de la Ontología.
  2. Mapea la ubicación devuelta contra la constante `BODY_LOCATIONS`.
  3. Genera el Embedding Vectorial del resultado y guárdalo.

## FASE 3: Motor de Cruce Bayesiano (The Matcher)
* **Acción:** Al desarrollar la clase `Matcher`, sigue estos 3 pasos:
  1. **Spatial Pruning (Poda):** Ejecuta una query SQL que descarte el 95% de los cuerpos basándose en Edad, Sexo y Macro-región anatómica.
  2. **Vector Similarity:** Usa Qdrant/FAISS para encontrar los N vectores más cercanos usando Similitud de Coseno.
  3. **Multi-Trait Bayesian Scoring:** Si un cuerpo tiene múltiples marcas que hacen match, no sumes linealmente. Aplica probabilidad condicional basada en el "Peso de Rareza".

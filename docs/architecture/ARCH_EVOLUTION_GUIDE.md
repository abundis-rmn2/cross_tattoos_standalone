# 🗺️ GUÍA DE EVOLUCIÓN DE ARQUITECTURA (C4 + PlantUML)

Tu objetivo es mantener la integridad visual y estructural de la arquitectura del Sistema Nacional mientras escala.

## 📋 Reglas de Actualización
1. **Sincronía Obligatoria**: Si creas un nuevo módulo o base de datos en código, DEBES proponer la actualización del archivo `docs/architecture/container_diagram.puml`.
2. **Proceso de Proyección**: Cuando proyectes un cambio (ej. "Añadir Padrón Nacional"), evalúa el impacto, genera el código PlantUML primero y justifica qué contenedor asume la nueva carga según SOLID.

## 🗄️ Disparadores de Escalamiento (Triggers Vectoriales)
Si los nuevos requerimientos cruzan estos umbrales, DEBES proponer cambios estructurales:
* **Volumen Masivo (> 5 Millones de Vectores):** Propón pasar de un nodo único a un **Clúster Distribuido (Sharding)** particionando por macro-regiones.
* **Latencia de Cruce (> 300ms):** Propón optimizaciones de índices (Cuantización de Vectores) advirtiendo explícitamente el trade-off entre velocidad y pérdida de precisión forense.

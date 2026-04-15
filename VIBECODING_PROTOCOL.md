# 🏄 PROTOCOLO DE DESARROLLO CON IA (VIBECODING)

La velocidad sin estructura es negligencia en un sistema forense. Define los límites de la generación automática de código.

## 🚧 1. El Mapa de Zonas Seguras
* 🟢 **ZONA VERDE (Vibecoding Libre):** `data_sources/adapters/`, `tests/`. (Libertad total para que la IA construya conectores para nuevos estados y genere mocks).
* 🟡 **ZONA AMARILLA (Guiado):** `processors/`. (Vigila de cerca que no use regex complejas y respete el `FORENSIC_ONTOLOGY.md`).
* 🔴 **ZONA ROJA (PROHIBIDO Vibecoding):** `core/` y `crossing/`. (El Dominio Bayesiano requiere diseño meticuloso. Un error aquí arruina la validez legal del proyecto).

## 🚦 2. El "Vibe Check" Arquitectónico
Antes de aceptar código masivo de la IA, verifica:
1. **¿Importó algo externo en `core/`?** RECHAZA.
2. **¿Creó un bucle anidado (for-for)?** RECHAZA. Pide Vector DB o Pandas Merge.
3. **¿Hardcodeó reglas (if-else masivos)?** RECHAZA. Pide el Patrón Strategy.

## 🛑 3. Regla de Oro Forense
**CERO DATOS REALES EN LA IA:** Está ESTRICTAMENTE PROHIBIDO pegar datos reales de expedientes forenses en los prompts. Usa datos dummy siempre. La responsabilidad legal del código generado es tuya.

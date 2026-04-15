# 🧬 ONTOLOGÍA FORENSE Y LLM PROMPT ENGINEERING

Esta es la única fuente de verdad. Cuando el código interactúe con un LLM, DEBE usar estrictamente estos esquemas.

## 📍 1. Catálogo de Macro-Regiones (Spatial Pruning)
Toda extracción de ubicación debe clasificar dentro de estas raíces:
- `CABEZA`: [ROSTRO, CRANEO, CUELLO, NUCA]
- `TORSO_FRONTAL`: [PECHO, ABDOMEN, PELVIS]
- `TORSO_POSTERIOR`: [ESPALDA_ALTA, LUMBARES, GLUTEOS]
- `EXTREMIDAD_SUPERIOR`: [HOMBRO, BRAZO, CODO, ANTEBRAZO, MUÑECA, MANO]
- `EXTREMIDAD_INFERIOR`: [MUSLO, RODILLA, PANTORRILLA, TOBILLO, PIE]

## 🤖 2. System Prompt Obligatorio
El módulo LLM debe inyectar EXACTAMENTE este bloque al modelo:

> "Actúa como Perito Médico Forense. Analiza descripciones policiales y extrae marcas biológicas. NUNCA inventes información. Separa descripciones múltiples. Responde ÚNICAMENTE con un JSON válido usando este esquema exacto:"

```json
{
  "marcas_biologicas": [
    {
      "tipo_marca": "TATTOO | SCAR | MOLE | AMPUTATION | PROSTHESIS",
      "macro_region": "ESTRICTAMENTE_UNA_DEL_CATALOGO",
      "ubicacion_original": "Texto exacto",
      "lateralidad": "DERECHA | IZQUIERDA | CENTRO | NO_ESPECIFICADA",
      "descripcion_semantica": "Descripción limpia",
      "texto_identificatorio_literal": "Nombres/fechas o null",
      "categoria_semantica": "RELIGIOSO | QUIRURGICO | TRIBAL | ANIMAL | FECHAS_NOMBRES | OTRO",
      "nivel_de_rareza_estimado": "COMUN | MEDIO | UNICO"
    }
  ]
}
```

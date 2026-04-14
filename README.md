# Cross Tattoos Standalone

Sistema independiente para identificación de personas desaparecidas mediante el cruce de descripciones de tatuajes entre registros PFSI (cuerpos no identificados) y REPD (personas desaparecidas) de Jalisco, México.

---

## 📋 Tabla de Contenidos

1. [Descripción General](#descripción-general)
2. [Flujo del Pipeline](#flujo-del-pipeline)
3. [Estructura del Proyecto](#estructura-del-proyecto)
4. [Instalación](#instalación)
5. [Configuración](#configuración)
6. [Archivos de Datos](#archivos-de-datos)
7. [Uso del CLI](#uso-del-cli)
8. [API Programática](#api-programática)
9. [Algoritmos](#algoritmos)

---

## 📖 Descripción General

Este módulo implementa un pipeline completo para:

1. **Minar datos** de dos fuentes:
   - **PFSI**: Portal de Ciencias Forenses de Jalisco (web scraping)
   - **REPD**: Registro Estatal de Personas Desaparecidas (API REST)

2. **Cruzar personas** basándose en:
   - Fecha (desaparición antes del hallazgo)
   - Sexo (coincidencia exacta)
   - Edad (tolerancia configurable)
   - Nombre (similitud por SequenceMatcher)
   - Ubicación (municipio)

3. **Categorizar tatuajes** extrayendo:
   - Ubicación corporal
   - Texto literal (nombres, fechas)
   - Categorías (religioso, animales, símbolos, etc.)
   - Palabras clave

4. **Cruzar tatuajes** calculando:
   - Similitud TF-IDF de descripciones
   - Similitud de ubicaciones corporales
   - Coincidencia exacta de texto

5. **Exportar resultados** a:
   - CSV (para análisis)
   - GraphML (para visualización de redes)

---

## 🔄 Flujo del Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    FUENTES DE DATOS                              │
├─────────────────────────────────────────────────────────────────┤
│  [Web PFSI] ──► pfsi_miner.py ──► MySQL ──► sql_exporter.py     │
│  [API REPD] ──► repd_miner.py ──► MySQL ──► sql_exporter.py     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATOS RAW (CSV)                               │
├─────────────────────────────────────────────────────────────────┤
│  data/raw/                                                       │
│  ├── pfsi_v2_principal.csv      (cuerpos no identificados)      │
│  ├── repd_vp_cedulas_principal.csv  (personas desaparecidas)    │
│  ├── repd_vp_cedulas_senas.csv      (tatuajes/señas)            │
│  └── repd_vp_cedulas_vestimenta.csv (vestimenta)                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CRUCE DE PERSONAS                             │
├─────────────────────────────────────────────────────────────────┤
│  crossing/person_matcher.py                                      │
│                                                                  │
│  Criterios:                                                      │
│  ✓ fecha_desaparicion < Fecha_Ingreso (obligatorio)             │
│  ✓ sexo == Sexo (obligatorio)                                   │
│  • edad ± 10 años (+1 punto)                                    │
│  • nombre_completo ~ Probable_nombre (+2 x similitud)           │
│  • municipio == Delegacion_IJCF (+0.5 puntos)                   │
│                                                                  │
│  Output: data/cross_examples/person_matches_name_age.csv        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CATEGORIZACIÓN DE TATUAJES                    │
├─────────────────────────────────────────────────────────────────┤
│  processors/categorizer_pfsi.py    processors/categorizer_repd.py│
│                                                                  │
│  Para cada tatuaje extrae:                                       │
│  • ubicacion: "BRAZO DERECHO", "ESPALDA"                        │
│  • texto_extraido: "MARIA", "15/09/1990"                        │
│  • categorias: "RELIGIOSO", "NOMBRES"                           │
│  • palabras_clave: "virgen", "cruz", "nombre"                   │
│                                                                  │
│  Output:                                                         │
│  ├── data/processed/tatuajes_procesados_PFSI.csv                │
│  └── data/processed/tatuajes_procesados_REPD.csv                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CRUCE DE TATUAJES                             │
├─────────────────────────────────────────────────────────────────┤
│  Modo Simple: crossing/tattoo_matcher_simple.py                  │
│  • Compara TODOS los tatuajes PFSI vs TODOS los REPD            │
│  • Muy lento (millones de comparaciones)                        │
│                                                                  │
│  Modo Strict: crossing/tattoo_matcher_strict.py                  │
│  • Solo compara tatuajes de pares ya identificados              │
│  • Mucho más rápido y preciso                                   │
│                                                                  │
│  Similitud combinada:                                            │
│  score = 0.5×TF-IDF + 0.3×ubicación + 0.2×texto_exacto          │
│                                                                  │
│  Output:                                                         │
│  ├── data/cross_examples/tattoo_matches.csv (simple)            │
│  └── data/cross_examples/tattoo_matches_strict.csv (strict)     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXPORTACIÓN                                   │
├─────────────────────────────────────────────────────────────────┤
│  exporters/graph_exporter.py                                     │
│                                                                  │
│  Nodos:                                                          │
│  • pfsi_{id} - cuerpo no identificado                           │
│  • repd_{id} - persona desaparecida                             │
│  • loc_{ubicacion} - ubicación corporal                         │
│                                                                  │
│  Aristas:                                                        │
│  • pfsi ──similarity──► repd (score de tatuaje)                 │
│  • pfsi ──located_at──► loc                                     │
│  • repd ──found_at──► loc                                       │
│                                                                  │
│  Output: data/output/tattoo_matches.graphml                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Estructura del Proyecto

```
cross_tattoos_standalone/
│
├── cli.py                    # CLI unificado (punto de entrada)
├── setup_data.py             # Script de configuración inicial
├── README.md                 # Esta documentación
│
├── config/                   # Configuración
│   ├── __init__.py
│   ├── settings.py           # Rutas, umbrales, API keys
│   ├── db_credentials.json   # Credenciales MySQL (gitignore)
│   ├── .env                  # API keys (gitignore)
│   └── *.example             # Templates
│
├── core/                     # Utilidades compartidas
│   ├── __init__.py
│   ├── data_loader.py        # Carga unificada de CSVs
│   ├── text_processor.py     # Preprocesamiento de texto
│   └── constants.py          # Ubicaciones, categorías, keywords
│
├── data_sources/             # Minado de datos
│   ├── __init__.py
│   ├── pfsi_miner.py         # Web scraping PFSI
│   ├── repd_miner.py         # API REPD
│   └── sql_exporter.py       # MySQL → CSV
│
├── processors/               # Categorización
│   ├── __init__.py
│   ├── base.py               # Clase base abstracta
│   ├── categorizer_pfsi.py   # Categoriza tatuajes PFSI
│   └── categorizer_repd.py   # Categoriza tatuajes REPD
│
├── crossing/                 # Algoritmos de cruce
│   ├── __init__.py
│   ├── person_matcher.py     # Cruce de personas
│   ├── tattoo_matcher_simple.py   # Cruce simple (todos vs todos)
│   └── tattoo_matcher_strict.py   # Cruce estricto (solo pares)
│
├── llm/                      # Integración LLM (DeepSeek)
│   ├── __init__.py
│   ├── deepseek_client.py        # Cliente API DeepSeek
│   ├── categorizer_pfsi_llm.py   # Categorización PFSI con LLM
│   └── categorizer_repd_llm.py   # Categorización REPD con LLM
│
├── exporters/                # Exportación
│   ├── __init__.py
│   └── graph_exporter.py     # CSV → GraphML
│
├── data/                     # Datos (gitignore)
│   ├── raw/                  # CSVs fuente
│   ├── processed/            # Tatuajes categorizados
│   ├── cross_examples/       # Resultados de cruces
│   └── output/               # GraphML y otros
│
└── venv/                     # Entorno virtual (gitignore)
```

---

## 🤖 Categorización con LLM (DeepSeek)

### ¿Por qué usar LLM?

Las descripciones de tatuajes son extremadamente inconsistentes:

| Problema | Ejemplo | Solución LLM |
|----------|---------|--------------|
| Múltiples tatuajes en una descripción | "Tiene virgen en brazo derecho y nombre MARIA en espalda" | Separa en 2 registros |
| Ubicaciones inconsistentes | "braso", "BRASO DER.", "brazo der" | Normaliza a "BRAZO DERECHO" |
| Texto no estructurado | "leyenda que dice maria 1990" | Extrae: texto="MARIA 1990" |
| Categorías implícitas | "imagen religiosa con ángel" | Detecta: RELIGIOSO, ANGELES |

### Uso con CLI

```bash
# Categorizar PFSI con LLM
python cli.py categorize pfsi --llm

# Categorizar REPD con LLM
python cli.py categorize repd --llm

# Limitar registros (para testing)
python cli.py categorize pfsi --llm --max 10

# Categorizar ambos con LLM
python cli.py categorize all --llm
```

### Uso Programático

```python
from llm.categorizer_pfsi_llm import PFSICategorizerLLM
from llm.categorizer_repd_llm import REPDCategorizerLLM

# PFSI
categorizer = PFSICategorizerLLM()
result_df = categorizer.run(max_records=100)  # Limitar para testing

# REPD
categorizer = REPDCategorizerLLM()
result_df = categorizer.run()
```

### Configuración DeepSeek

1. Obtener API key en: https://platform.deepseek.com/
2. Configurar en `config/.env`:
   ```env
   DEEPSEEK_API_KEY=sk-xxxxxxxxxxxx
   ```

### Archivos generados con LLM

| Archivo | Ubicación | Descripción |
|---------|-----------|-------------|
| `llm_tatuajes_procesados_PFSI.csv` | `data/processed/` | Tatuajes PFSI categorizados con LLM |
| `llm_tatuajes_procesados_REPD.csv` | `data/processed/` | Tatuajes REPD categorizados con LLM |
| `checkpoint_*_llm_N.csv` | `data/processed/` | Checkpoints cada 50 registros |

### Prompt utilizado

El modelo recibe instrucciones específicas para:

```
1. Separar múltiples tatuajes en registros individuales
2. Estandarizar ubicaciones EN MAYÚSCULAS
3. Extraer texto literal (nombres, fechas)
4. Asignar categorías: RELIGIOSO, ANIMALES, SIMBOLOS, NOMBRES_FECHAS, 
   TRIBAL, NATURALEZA, LETRAS_NUMEROS, CORAZONES, CALAVERAS, OTROS
5. Devolver JSON estructurado
```

### Comparación: Reglas vs LLM

| Aspecto | Reglas | LLM |
|---------|--------|-----|
| **Velocidad** | Muy rápido (~segundos) | Lento (~1-2 seg/registro) |
| **Costo** | Gratis | ~$0.001/registro |
| **Precisión** | Media (patrones fijos) | Alta (comprensión semántica) |
| **Mantenimiento** | Agregar reglas manualmente | Automático |
| **Casos nuevos** | Falla con variantes | Se adapta |

### Recomendación

1. **Para datasets pequeños (<500 registros)**: Usar LLM
2. **Para datasets grandes**: Usar reglas, luego LLM solo para errores
3. **Para producción**: Procesar con LLM una vez, guardar resultados

### Comandos con soporte LLM

| Comando | Opción | Descripción |
|---------|--------|-------------|
| `categorize pfsi` | `--llm` | Categoriza PFSI con DeepSeek |
| `categorize repd` | `--llm` | Categoriza REPD con DeepSeek |
| `categorize all` | `--llm` | Categoriza ambos con DeepSeek |
| `categorize *` | `--max N` | Limita a N registros (testing) |
| `cross-tattoos strict` | `--llm` | Usa datasets LLM para matching |
| `cross-tattoos simple` | `--llm` | Usa datasets LLM para matching |

---

## 🔧 Instalación

### Opción 1: Setup automático (recomendado)

```bash
cd cross_tattoos_standalone

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install pandas numpy scikit-learn networkx click tqdm \
            python-dotenv requests beautifulsoup4 mysql-connector-python

# Ejecutar setup (copia CSVs y credenciales desde proyecto original)
python setup_data.py
```

### Opción 2: Manual

```bash
# 1. Crear entorno virtual
python -m venv venv && source venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt  # si existe

# 3. Copiar credenciales
cp /ruta/a/db_credentials.json config/
cp /ruta/a/.env config/

# 4. Copiar CSVs
cp /ruta/a/csv/equi/*.csv data/raw/
```

---

## ⚙️ Configuración

### config/db_credentials.json

```json
{
    "host": "localhost",
    "user": "tu_usuario",
    "password": "tu_contraseña",
    "database": "tu_base_de_datos"
}
```

### config/.env

```env
DEEPSEEK_API_KEY=sk-xxx...  # Para categorización con LLM
GOOGLE_API_KEY=xxx...        # Para geocodificación (opcional)
```

### config/settings.py - Parámetros configurables

| Parámetro | Valor Default | Descripción |
|-----------|---------------|-------------|
| `SIMILARITY_THRESHOLD` | 0.6 | Umbral mínimo de similitud para considerar match |
| `NAME_SIMILARITY_THRESHOLD` | 0.5 | Umbral para similitud de nombres |
| `AGE_TOLERANCE` | 10 | Años de tolerancia en comparación de edad |
| `TEXT_WEIGHT` | 0.5 | Peso del TF-IDF en score combinado |
| `LOCATION_WEIGHT` | 0.3 | Peso de ubicación corporal |
| `EXACT_MATCH_WEIGHT` | 0.2 | Peso de coincidencia exacta de texto |

---

## 📊 Archivos de Datos

### Archivos REQUERIDOS (entrada)

| Archivo | Ubicación | Descripción | Columnas clave |
|---------|-----------|-------------|----------------|
| `pfsi_v2_principal.csv` | `data/raw/` | Cuerpos no identificados | ID, Fecha_Ingreso, Sexo, Edad, Tatuajes |
| `repd_vp_cedulas_principal.csv` | `data/raw/` | Personas desaparecidas | id_cedula_busqueda, nombre_completo, sexo, edad_momento_desaparicion |
| `repd_vp_cedulas_senas.csv` | `data/raw/` | Señas particulares/tatuajes | id_cedula_busqueda, tipo_sena, descripcion, parte_cuerpo |

### Archivos GENERADOS (intermedio)

| Archivo | Ubicación | Generado por |
|---------|-----------|--------------|
| `tatuajes_procesados_PFSI.csv` | `data/processed/` | `categorizer_pfsi.py` |
| `tatuajes_procesados_REPD.csv` | `data/processed/` | `categorizer_repd.py` |

### Archivos EXPORTADOS (salida)

| Archivo | Ubicación | Generado por | Descripción |
|---------|-----------|--------------|-------------|
| `person_matches_name_age.csv` | `data/cross_examples/` | `person_matcher.py` | Pares persona-cuerpo probables |
| `tattoo_matches.csv` | `data/cross_examples/` | `tattoo_matcher_simple.py` | Matches de tatuajes (simple) |
| `tattoo_matches_strict.csv` | `data/cross_examples/` | `tattoo_matcher_strict.py` | Matches de tatuajes (estricto) |
| `tattoo_matches.graphml` | `data/output/` | `graph_exporter.py` | Grafo para visualización |

---

## 💻 Uso del CLI

### Ver ayuda
```bash
python cli.py --help
python cli.py mine --help
python cli.py categorize --help
```

### Pipeline completo
```bash
# Con minado y export SQL
python cli.py run-all

# Sin minado (usando CSVs existentes)
python cli.py run-all --skip-mine --skip-export
```

### Comandos individuales

```bash
# 1. Setup inicial
python cli.py setup

# 2. Minar datos (si tienes acceso a web/API)
python cli.py mine pfsi --start-date 01/01/2020 --end-date 31/12/2024
python cli.py mine repd --limit 1000

# 3. Exportar SQL a CSV
python cli.py export-sql --all

# 4. Cruzar personas
python cli.py cross-persons

# 5. Categorizar tatuajes (reglas o LLM)
python cli.py categorize all          # Con reglas (rápido)
python cli.py categorize all --llm    # Con DeepSeek LLM (mejor calidad)
python cli.py categorize pfsi --llm --max 100  # Limitar para testing

# 6. Cruzar tatuajes
python cli.py cross-tattoos strict          # Con datasets de reglas
python cli.py cross-tattoos strict --llm    # Con datasets de LLM (mejor)
python cli.py cross-tattoos simple          # Todos vs todos (muy lento)

# 7. Exportar a GraphML
python cli.py export-graph --strict
```

### Pipeline completo con LLM

```bash
# Paso 1: Categorizar con LLM (mejor calidad, ~1-2h)
python cli.py categorize all --llm

# Paso 2: Cruzar usando datasets LLM
python cli.py cross-tattoos strict --llm

# Paso 3: Exportar resultados
python cli.py export-graph --strict
```

---

## 🐍 API Programática

```python
from config.settings import Config
from core.data_loader import DataLoader
from crossing.person_matcher import PersonMatcher
from crossing.tattoo_matcher_strict import StrictTattooMatcher
from processors.categorizer_pfsi import PFSICategorizer
from exporters.graph_exporter import GraphExporter

# Setup
Config.ensure_dirs()

# 1. Cargar datos
pfsi_df = DataLoader.load_pfsi_raw()
repd_df = DataLoader.load_repd_cedulas()

# 2. Cruzar personas
matcher = PersonMatcher()
person_matches = matcher.run()

# 3. Categorizar tatuajes
PFSICategorizer().run()
REPDCategorizer().run()

# 4. Cruzar tatuajes
tattoo_matcher = StrictTattooMatcher()
tattoo_matches, person_pairs = tattoo_matcher.run()

# 5. Exportar grafo
GraphExporter().run(strict=True)
```

---

## 🧮 Algoritmos

### Cruce de Personas

```python
# Filtros obligatorios
if fecha_desaparicion >= Fecha_Ingreso:
    continue  # La persona desapareció DESPUÉS del hallazgo
if sexo != Sexo:
    continue  # Sexo no coincide

# Puntuación
score = 0
if edad_en_rango(missing_age, body_age, ±10):
    score += 1
if nombre_similar(missing_name, body_name) > 0.5:
    score += similitud * 2
if municipio == delegacion:
    score += 0.5
```

### Similitud de Tatuajes (TF-IDF)

```python
# 1. Crear características combinadas
features = f"{descripcion} {ubicacion} {categorias}"

# 2. Vectorizar con TF-IDF
vectorizer = TfidfVectorizer()
pfsi_vectors = vectorizer.fit_transform(pfsi_features)
repd_vectors = vectorizer.transform(repd_features)

# 3. Calcular similitud
text_sim = cosine_similarity(pfsi_vec, repd_vec)
loc_sim = cosine_similarity(pfsi_loc, repd_loc)
exact_match = 1 if pfsi_text == repd_text else 0

# 4. Score combinado
score = 0.5*text_sim + 0.3*loc_sim + 0.2*exact_match
```

### Categorías de Tatuajes

- **RELIGIOSO**: virgen, cruz, ángel, rosario, jesús
- **ANIMALES**: águila, león, lobo, serpiente, mariposa
- **SÍMBOLOS**: estrella, corazón, infinito, calavera
- **NOMBRES**: detectados entre comillas o mayúsculas
- **FECHAS**: patrones DD/MM/YYYY o similares
- **TRIBALES**: tribal, azteca, maya, celta

---

## ⚠️ Notas Importantes

1. **Gitignore**: Añadir al `.gitignore` del proyecto padre:
   ```gitignore
   cross_tattoos_standalone/data/
   cross_tattoos_standalone/config/.env
   cross_tattoos_standalone/config/db_credentials.json
   cross_tattoos_standalone/venv/
   ```

2. **Tiempo de ejecución**: 
   - Cruce de personas: ~20-30 min (3000+ x 4000+ comparaciones)
   - Cruce estricto de tatuajes: ~5-10 min
   - Cruce simple de tatuajes: Horas (no recomendado)

3. **Memoria**: Los DataFrames pueden consumir >1GB RAM con datasets completos.

---

## 📄 Licencia

Este proyecto es para uso educativo e investigación en identificación de personas.

---

## 🤝 Contribución

Fork del proyecto original `HerramientasDeTejer` sin modificar el código fuente original.

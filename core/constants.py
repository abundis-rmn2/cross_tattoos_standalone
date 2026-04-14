"""
Cross Tattoos Standalone - Constants

Centralized constants for body locations, tattoo categories, and keywords.
Extracted from cat_tattoo_PFSI.py and cat_tattoo_RPED.py
"""

# Body locations where tattoos can be found
BODY_LOCATIONS = [
    'ROSTRO', 'CUERPO', 'BRAZO', 'HOMBRO', 'MANO', 'PIERNA', 'TORSO', 'ESCAPULA',
    'CABEZA', 'CLAVICULA', 'PECTORAL', 'FLANCO', 'ANTEBRAZO', 'OJO', 'CARA', 'CUELLO',
    'ESPALDA', 'EXTREMIDAD', 'MUSLO', 'RODILLA', 'DORSO', 'ABDOMEN', 'TORAX',
    'MUÑECA', 'OREJA', 'PECHO', 'COSTADO', 'PANTORRILLA', 'DORSAL', 'CRANEO', 'PULGAR',
    'DEDOS', 'INDICE', 'MEÑIQUE', 'TOBILLO', 'CADERA', 'LENGUA', 'NARIZ', 'CEJA',
    'BUSTO', 'CODO', 'FALANGE', 'LUMBAR', 'TALON', 'PLANTA', 'NUCA', 'OMBLIGO',
    'PALMA', 'GLÚTEO', 'ENTREPIERNA', 'INGLE', 'ESPINILLA', 'LABIO', 'MEJILLA',
    'SENO', 'HUESO', 'TRAPECIO', 'INTERCOSTAL', 'AXILA', 'PIE', 'TALÓN', 'EMPEINE',
    'DEDO GORDO', 'NUDILLO', 'COSTILLAS'
]

# Laterality terms
LATERALITY = ['DERECHO', 'DERECHA', 'IZQUIERDO', 'IZQUIERDA']

# Tattoo categories with associated keywords
TATTOO_CATEGORIES = {
    "Figura Humana": [
        "rostro", "figura", "hombre", "mujer", "persona", "cuerpo", "ojos", 
        "silueta", "humana", "humano", "cráneo", "calavera", "busto", 
        "caricatura", "personaje"
    ],
    
    "Letras-Números": [
        "letra", "números", "leyenda", "palabras", "texto", "nombre", "frase",
        "cursiva", "manuscrita", "mayúsculas", "cursivo", "tipografía", 
        "tipologia", "script", "leyendas", "numeros", "romanos", "cursivas",
        "letras", "palabra", "tipografia", "mayusculas"
    ],
    
    "Simbolos": [
        "símbolo", "cruz", "rojo", "negro", "símbolos", "machete", "corazón",
        "estrella", "infinito", "triángulo", "cruz cristiana", "corazon",
        "corazones", "estrellas", "triangulo", "círculo", "circulo",
        "geométrico", "geométricos", "guadaña", "ancla", "flecha", "espada",
        "daga", "signo", "trébol", "trebol", "diamante", "asterisco",
        "asteriscos", "piramide", "playboy", "atrapasueños", "brujula",
        "mandala", "yin", "yang", "ying", "calendario", "egipcio", "baraja",
        "carta", "cartas", "reloj", "bandera", "logotipo", "logo", "alegoría",
        "alegoria"
    ],
    
    "Animales": [
        "tigre", "león", "zorro", "lobo", "perro", "gallo", "pez", "pájaro",
        "conejo", "águila", "aguila", "serpiente", "dragón", "dragon",
        "mariposa", "pantera", "gato", "felino", "buho", "búho", "aves", "ave",
        "cobra", "alacrán", "alacran", "escorpión", "araña", "pavo", "paloma",
        "colibrí", "colibri", "tortuga", "ballena", "delfín", "delfin",
        "murciélago", "murcielago", "halcón", "halcon", "leopardo", "jaguar",
        "rinoceronte", "elefante", "tiburón", "tiburon", "orca"
    ],
    
    "Religiosos": [
        "santa muerte", "cruz cristiana", "anj", "horus", "dios", "ángel",
        "santo", "religión", "virgen", "jesús", "jesucristo", "cristo",
        "maría", "guadalupe", "san", "judas", "sagrado", "oración", "oracion",
        "rosario", "biblia", "santísima", "santisima", "santos", "ángeles",
        "demonios", "demonio", "diablo", "infierno", "cielo", "paraíso",
        "paraiso", "altar", "templo", "iglesia", "católica", "catolica",
        "buda", "zen", "yoga", "meditación", "meditacion", "karma", "chakra",
        "om", "símbolo religioso", "simbolo religioso"
    ],
    
    "Nombre": [
        "jose", "alberto", "juan", "adriana", "carlos", "maria", "luis", "ana",
        "david", "eduardo", "martha", "victor", "tadeo", "alejandra", "santiago",
        "alejandro", "laura", "raul", "lopez", "silvia", "jesus"
    ],
    
    "Otros": [
        "irreconocible", "indeterminado", "abstracto", "floral", "combinado",
        "fantasía", "manga", "cuerno", "flores", "planta", "hojas", "ramas",
        "árbol", "arbol", "paisaje", "naturaleza", "sol", "luna", "estrella",
        "estrellas", "cielo", "nube", "mar", "océano", "oceano", "montaña",
        "montana", "fuego", "llamas", "agua", "tierra", "viento", "rayo",
        "trueno", "arcoíris", "arcoiris", "galaxia", "universo", "planeta",
        "cometa", "espacio", "cosmos", "alien", "ovni", "robot", "futurista",
        "retro", "vintage", "moderno", "arte", "dibujo", "pintura", "grafiti",
        "graffiti", "mural"
    ]
}

# Patterns for splitting tattoo descriptions
TATTOO_SPLIT_PATTERNS = {
    'numbered': r'\d+\.-|\d+\)',
    'separator': '-',
    'comma': ','
}

# Words to skip when splitting tattoos
SKIP_WORDS = ['TATUAJE', 'LOCALIZADO', 'EN']

# Terms that indicate no tattoos
NO_TATTOO_TERMS = ['No presenta', 'NO PRESENTA', 'Sin tatuajes', 'SIN TATUAJES']
# Anatomical proximity groups for fuzzy location matching
ANATOMICAL_PROXIMITY = {
    'MANO': ['MUÑECA', 'DEDOS', 'DORSO', 'PALMA', 'NUDILLO', 'PULGAR', 'INDICE', 'MEÑIQUE', 'FALANGE'],
    'MUÑECA': ['MANO', 'ANTEBRAZO'],
    'ANTEBRAZO': ['MUÑECA', 'CODO', 'BRAZO'],
    'BRAZO': ['ANTEBRAZO', 'CODO', 'HOMBRO'],
    'HOMBRO': ['BRAZO', 'CUELLO', 'ESPALDA', 'CLAVICULA', 'PECTORAL'],
    'PECTORAL': ['HOMBRO', 'PECHO', 'TORAX', 'CLAVICULA', 'ESTERNON'],
    'PECHO': ['PECTORAL', 'TORAX', 'ABDOMEN', 'SENO', 'COSTILLAS'],
    'ABDOMEN': ['PECHO', 'TORAX', 'COSTADO', 'FLANCO', 'OMBLIGO', 'CADERA'],
    'ESPALDA': ['HOMBRO', 'NUCA', 'DORSAL', 'LUMBAR', 'ESCAPULA', 'TRAPECIO'],
    'PIERNA': ['MUSLO', 'RODILLA', 'PANTORRILLA', 'ESPINILLA'],
    'MUSLO': ['PIERNA', 'CADERA', 'INGLE', 'RODILLA'],
    'RODILLA': ['MUSLO', 'PANTORRILLA', 'ESPINILLA'],
    'PANTORRILLA': ['RODILLA', 'ESPINILLA', 'TOBILLO'],
    'TOBILLO': ['PANTORRILLA', 'ESPINILLA', 'PIE'],
    'PIE': ['TOBILLO', 'TALON', 'PLANTA', 'EMPEINE', 'DEDO GORDO'],
    'CUELLO': ['NUCA', 'GARGANTA', 'HOMBRO', 'CARA'],
    'ROSTRO': ['CARA', 'FRENTE', 'MEJILLA', 'NARIZ', 'LABIO', 'MENTON', 'CEJA', 'OJO', 'OREJA'],
    'CEJA': ['OJO', 'FRENTE'],
    'LABIO': ['BOCA', 'MENTON', 'NARIZ'],
}

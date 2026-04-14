"""
Cross Tattoos Standalone - Centralized Configuration

All paths, thresholds, and settings are defined here to avoid
hardcoded values across the codebase.
"""

from pathlib import Path
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Central configuration for Cross Tattoos Standalone module."""
    
    # Base paths
    BASE_DIR = Path(__file__).parent.parent
    CONFIG_DIR = BASE_DIR / "config"
    DATA_DIR = BASE_DIR / "data"
    
    # Data subdirectories
    RAW_DIR = DATA_DIR / "raw"
    PROCESSED_DIR = DATA_DIR / "processed"
    OUTPUT_DIR = DATA_DIR / "output"
    CROSS_EXAMPLES_DIR = DATA_DIR / "cross_examples"
    
    # Source files (raw data)
    PFSI_FILE = RAW_DIR / "pfsi_v2_principal.csv"
    REPD_CEDULAS = RAW_DIR / "repd_vp_cedulas_principal.csv"
    REPD_SENAS = RAW_DIR / "repd_vp_cedulas_senas.csv"
    REPD_VESTIMENTA = RAW_DIR / "repd_vp_cedulas_vestimenta.csv"
    
    # Processed files (categorized tattoos)
    PFSI_TATTOOS = PROCESSED_DIR / "tatuajes_procesados_PFSI.csv"
    REPD_TATTOOS = PROCESSED_DIR / "tatuajes_procesados_REPD.csv"
    LLM_PFSI_TATTOOS = PROCESSED_DIR / "llm_tatuajes_procesados_PFSI.csv"
    LLM_REPD_TATTOOS = PROCESSED_DIR / "llm_tatuajes_procesados_REPD.csv"
    
    # Cross-reference files
    PERSON_MATCHES = CROSS_EXAMPLES_DIR / "person_matches_name_age.csv"
    TATTOO_MATCHES = CROSS_EXAMPLES_DIR / "tattoo_matches.csv"
    TATTOO_MATCHES_STRICT = CROSS_EXAMPLES_DIR / "tattoo_matches_strict.csv"
    
    # Output files
    GRAPH_OUTPUT = OUTPUT_DIR / "tattoo_matches.graphml"
    
    # Database credentials - search in multiple locations
    DB_CREDENTIALS_FILE = CONFIG_DIR / "db_credentials.json"
    
    # Fallback paths for credentials (original project locations)
    DB_CREDENTIALS_FALLBACK_PATHS = [
        CONFIG_DIR / "db_credentials.json",                              # Local config
        BASE_DIR.parent / "db_credentials.json",                         # Project root
        Path.home() / "PycharmProjects" / "HopeisHope" / "db_credentials.json",  # Original project
    ]
    
    # API Keys (from environment)
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    # PFSI Scraping configuration
    PFSI_URL = "http://consultas.cienciasforenses.jalisco.gob.mx/buscarpfsi_v2.php"
    PFSI_DEFAULT_START_DATE = "01/11/2018"
    PFSI_DEFAULT_END_DATE = "30/11/2024"
    
    # REPD API configuration
    REPD_API_BASE_URL = "https://repd.jalisco.gob.mx/api/v1/version_publica/repd-version-publica-cedulas-busqueda/"
    REPD_DEFAULT_LIMIT = 1000
    REPD_PAUSE_TIME = 2  # seconds between API calls
    
    # Matching thresholds
    SIMILARITY_THRESHOLD = 0.6
    NAME_SIMILARITY_THRESHOLD = 0.5
    AGE_TOLERANCE = 10  # years
    
    # TF-IDF weights for refined combined similarity score
    TEXT_WEIGHT = 0.4
    LOCATION_WEIGHT = 0.2
    CATEGORY_WEIGHT = 0.15
    KEYWORD_WEIGHT = 0.15
    EXACT_MATCH_WEIGHT = 0.1
    
    # LLM Configuration
    DEEPSEEK_MODEL = "deepseek-chat"
    LLM_MAX_TOKENS = 5000
    LLM_TEMPERATURE = 0.7
    
    @classmethod
    def ensure_dirs(cls):
        """Create all data directories if they don't exist."""
        dirs = [
            cls.RAW_DIR,
            cls.PROCESSED_DIR,
            cls.OUTPUT_DIR,
            cls.CROSS_EXAMPLES_DIR
        ]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Data directories ensured at: {cls.DATA_DIR}")
    
    @classmethod
    def get_db_config(cls):
        """Load database configuration from JSON file, searching multiple locations."""
        # Search in fallback paths
        credentials_file = None
        for path in cls.DB_CREDENTIALS_FALLBACK_PATHS:
            if path.exists():
                credentials_file = path
                print(f"Using DB credentials from: {path}")
                break
        
        if credentials_file is None:
            raise FileNotFoundError(
                f"Database credentials not found in any of these locations:\n"
                + "\n".join(f"  - {p}" for p in cls.DB_CREDENTIALS_FALLBACK_PATHS)
            )
        
        with open(credentials_file, 'r') as f:
            config = json.load(f)
        
        # Return only DB-related keys (exclude API keys)
        return {
            'host': config.get('host'),
            'user': config.get('user'),
            'password': config.get('password'),
            'database': config.get('database')
        }
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is present."""
        issues = []
        warnings = []
        
        # Check API keys
        if not cls.DEEPSEEK_API_KEY:
            warnings.append("DEEPSEEK_API_KEY not found in environment (LLM features disabled)")
        
        # Check DB credentials in fallback paths
        db_found = False
        for path in cls.DB_CREDENTIALS_FALLBACK_PATHS:
            if path.exists():
                db_found = True
                print(f"✓ DB credentials found at: {path}")
                break
        
        if not db_found:
            issues.append("DB credentials not found in any location")
        
        # Print results
        if warnings:
            print("Warnings:")
            for w in warnings:
                print(f"  ⚠️  {w}")
        
        if issues:
            print("Errors:")
            for issue in issues:
                print(f"  ✗ {issue}")
        
        if not issues and not warnings:
            print("✓ Configuration validated successfully")
        
        return len(issues) == 0

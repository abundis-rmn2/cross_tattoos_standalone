"""
Cross Tattoos Standalone - Data Loader

Unified data loading functions for CSV files.
Forked from: cross_persons/load_all.py
"""

import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import Config


class DataLoader:
    """Unified data loader for all CSV files in the pipeline."""
    
    @staticmethod
    def load_pfsi_raw():
        """Load raw PFSI principal data."""
        path = Config.PFSI_FILE
        if not path.exists():
            raise FileNotFoundError(f"PFSI file not found: {path}")
        
        df = pd.read_csv(path)
        print(f"Loaded PFSI raw data: {df.shape}")
        return df
    
    @staticmethod
    def load_repd_cedulas():
        """Load REPD cedulas principal data."""
        path = Config.REPD_CEDULAS
        if not path.exists():
            raise FileNotFoundError(f"REPD cedulas file not found: {path}")
        
        df = pd.read_csv(path)
        print(f"Loaded REPD cedulas: {df.shape}")
        return df
    
    @staticmethod
    def load_repd_senas():
        """Load REPD senas particulares data."""
        path = Config.REPD_SENAS
        if not path.exists():
            raise FileNotFoundError(f"REPD senas file not found: {path}")
        
        df = pd.read_csv(path)
        print(f"Loaded REPD senas: {df.shape}")
        return df
    
    @staticmethod
    def load_repd_vestimenta():
        """Load REPD vestimenta data."""
        path = Config.REPD_VESTIMENTA
        if not path.exists():
            raise FileNotFoundError(f"REPD vestimenta file not found: {path}")
        
        df = pd.read_csv(path)
        print(f"Loaded REPD vestimenta: {df.shape}")
        return df
    
    @staticmethod
    def load_pfsi_tattoos(use_llm=False):
        """Load processed PFSI tattoos data."""
        path = Config.LLM_PFSI_TATTOOS if use_llm else Config.PFSI_TATTOOS
        if not path.exists():
            raise FileNotFoundError(f"PFSI tattoos file not found: {path}")
        
        df = pd.read_csv(path)
        print(f"Loaded PFSI tattoos ({'LLM' if use_llm else 'rule-based'}): {df.shape}")
        return df
    
    @staticmethod
    def load_repd_tattoos(use_llm=False):
        """Load processed REPD tattoos data."""
        path = Config.LLM_REPD_TATTOOS if use_llm else Config.REPD_TATTOOS
        if not path.exists():
            raise FileNotFoundError(f"REPD tattoos file not found: {path}")
        
        df = pd.read_csv(path)
        print(f"Loaded REPD tattoos ({'LLM' if use_llm else 'rule-based'}): {df.shape}")
        return df
    
    @staticmethod
    def load_person_matches():
        """Load person matches (cross-reference results)."""
        path = Config.PERSON_MATCHES
        if not path.exists():
            raise FileNotFoundError(f"Person matches file not found: {path}")
        
        df = pd.read_csv(path)
        print(f"Loaded person matches: {df.shape}")
        return df
    
    @staticmethod
    def load_tattoo_matches(strict=False):
        """Load tattoo matches results."""
        path = Config.TATTOO_MATCHES_STRICT if strict else Config.TATTOO_MATCHES
        if not path.exists():
            raise FileNotFoundError(f"Tattoo matches file not found: {path}")
        
        df = pd.read_csv(path)
        print(f"Loaded tattoo matches ({'strict' if strict else 'simple'}): {df.shape}")
        return df
    
    @classmethod
    def load_all_raw(cls):
        """Load all raw data files and return as dictionary."""
        dataframes = {}
        
        try:
            dataframes['pfsi'] = cls.load_pfsi_raw()
        except FileNotFoundError as e:
            print(f"Warning: {e}")
        
        try:
            dataframes['cedulas'] = cls.load_repd_cedulas()
        except FileNotFoundError as e:
            print(f"Warning: {e}")
        
        try:
            dataframes['senas'] = cls.load_repd_senas()
        except FileNotFoundError as e:
            print(f"Warning: {e}")
        
        try:
            dataframes['vestimenta'] = cls.load_repd_vestimenta()
        except FileNotFoundError as e:
            print(f"Warning: {e}")
        
        return dataframes
    
    @classmethod
    def load_for_tattoo_matching(cls, use_llm=False):
        """Load data required for tattoo matching pipeline."""
        return {
            'pfsi_tattoos': cls.load_pfsi_tattoos(use_llm),
            'repd_tattoos': cls.load_repd_tattoos(use_llm),
            'person_matches': cls.load_person_matches()
        }


# For backwards compatibility
def load_csv_files():
    """Legacy function - use DataLoader.load_all_raw() instead."""
    return DataLoader.load_all_raw()

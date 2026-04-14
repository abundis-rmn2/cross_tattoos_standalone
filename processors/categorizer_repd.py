"""
Cross Tattoos Standalone - REPD Categorizer

Rule-based tattoo categorizer for REPD data.
Forked from: cross_tattoos/cat_tattoo_RPED.py
"""

import pandas as pd
import re
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import Config
from core.data_loader import DataLoader
from core.text_processor import TextProcessor
from processors.base import BaseCategorizer


class REPDCategorizer(BaseCategorizer):
    """Rule-based categorizer for REPD tattoo descriptions."""
    
    def load_data(self):
        """Load REPD senas data (contains tattoo descriptions)."""
        try:
            return DataLoader.load_repd_senas()
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return None
    
    def split_tattoos(self, text):
        """
        Split multiple tattoo descriptions into individual tattoos.
        
        Args:
            text: Combined tattoo description text
            
        Returns:
            List of individual tattoo descriptions
        """
        if pd.isna(text):
            return []
        
        # Normalize quotes
        text = TextProcessor.normalize_quotes(text)
        
        # If description has numbered items
        if re.search(r'\d+\.-|\d+\)', text):
            parts = re.split(r'\d+\.-|\d+\)', text)
        # Split by semicolon
        elif ";" in text:
            parts = [p.strip() for p in text.split(";") if p.strip()]
        # Split by comma
        elif "," in text:
            parts = [p.strip() for p in text.split(",")]
        else:
            parts = [text]
        
        # Clean up parts
        clean_parts = []
        for part in parts:
            part = part.strip()
            if part and len(part) > 3 and not re.match(r'^\d{1,4}$', part):
                clean_parts.append(part)
        
        return clean_parts
    
    def process(self, df):
        """
        Process REPD data to categorize tattoos.
        
        Args:
            df: DataFrame with REPD senas data
            
        Returns:
            DataFrame with processed tattoos
        """
        print(f"Loaded DataFrame with shape: {df.shape}")
        
        # Filter for tattoo entries only (tipo_sena contains 'TATUAJE')
        if 'tipo_sena' in df.columns:
            # Accept both 'TATUAJE' and 'TATUAJES'
            tattoo_df = df[df['tipo_sena'].str.upper().str.contains('TATUAJE', na=False)].copy()
        else:
            # Fall back to description column if tipo_sena is not available
            tattoo_df = df[df['descripcion'].notna()].copy()
        
        print(f"Found {len(tattoo_df)} entries with tattoos")
        
        all_tattoos = []
        
        # Process each tattoo entry
        for _, row in tattoo_df.iterrows():
            person_id = row.get('id_cedula_busqueda', row.get('id', 'unknown'))
            description = row.get('descripcion', '')
            body_part = row.get('parte_cuerpo', '')
            
            if pd.isna(description) or not description:
                continue
            
            # Split description into individual tattoos
            individual_tattoos = self.split_tattoos(description)
            
            for tattoo in individual_tattoos:
                if len(tattoo) < 3:
                    continue
                
                # Extract information
                categories, keywords = self.categorize_keywords(tattoo)
                
                # Use body part from data if available, otherwise extract
                location = body_part if body_part else self.extract_location(tattoo)
                text = TextProcessor.extract_text_in_quotes(tattoo)
                
                all_tattoos.append({
                    'id_persona': person_id,
                    'descripcion_original': description,
                    'descripcion_tattoo': tattoo,
                    'ubicacion': location,
                    'texto_extraido': text,
                    'categorias': ', '.join(categories),
                    'palabras_clave': ', '.join(keywords)
                })
        
        result_df = pd.DataFrame(all_tattoos)
        print(f"Created DataFrame with {len(result_df)} individual tattoos")
        
        return result_df
    
    def save_results(self, df, output_path=None):
        """
        Save processed results to CSV.
        
        Args:
            df: DataFrame with processed tattoos
            output_path: Optional custom output path
            
        Returns:
            Path to saved file
        """
        if output_path is None:
            Config.ensure_dirs()
            output_path = Config.REPD_TATTOOS
        
        df.to_csv(output_path, index=False)
        print(f"Results saved to {output_path}")
        
        return output_path


def main():
    """Main entry point for REPD categorization."""
    categorizer = REPDCategorizer()
    return categorizer.run()


if __name__ == "__main__":
    main()

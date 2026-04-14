"""
Cross Tattoos Standalone - PFSI Categorizer

Rule-based tattoo categorizer for PFSI data.
Forked from: cross_tattoos/cat_tattoo_PFSI.py
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
from core.constants import NO_TATTOO_TERMS
from processors.base import BaseCategorizer


class PFSICategorizer(BaseCategorizer):
    """Rule-based categorizer for PFSI tattoo descriptions."""
    
    def load_data(self):
        """Load PFSI raw data."""
        try:
            return DataLoader.load_pfsi_raw()
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
        
        # If description has numbered items (like "1.-", "2.-", etc.)
        if re.search(r'\d+\.-|\d+\)', text):
            parts = re.split(r'\d+\.-|\d+\)', text)
        # Split by dash if present (but not in compound words)
        elif "-" in text and "LETRAS-NUMEROS" not in text and "LETRAS-NÚMEROS" not in text:
            parts = [p.strip() for p in text.split("-") if p.strip()]
        # Split by comma if present
        elif "," in text:
            parts = [p.strip() for p in text.split(",")]
        else:
            # If we can't split, treat as a single tattoo
            parts = [text]
        
        # Clean up parts
        clean_parts = []
        for part in parts:
            part = part.strip()
            
            # Skip short parts or those that are just numbers
            if part and len(part) > 3 and not re.match(r'^\d{1,4}$', part):
                # Remove any prefixes like "TATUAJE"
                if part.upper().startswith("TATUAJE "):
                    part = part[8:].strip()
                # Remove any location prefixes like "EN"
                if part.upper().startswith("EN "):
                    part = part[3:].strip()
                # Remove initial space after a dash
                if part.startswith("- "):
                    part = part[2:].strip()
                
                # Skip parts that are just generic words
                if part.upper() not in ["TATUAJE", "LOCALIZADO"]:
                    clean_parts.append(part)
        
        return clean_parts
    
    def parse_palabras_clave(self, text):
        """
        Extract palabras clave from PFSI format descriptions.
        
        Args:
            text: Description text that may contain PALABRAS CLAVE section
            
        Returns:
            List of keywords
        """
        if pd.isna(text):
            return []
        
        # Look for keyword section
        match = re.search(r'PALABRAS CLAVE:\s*(.*?)(?:\s*$|(?=\-))', text, re.IGNORECASE)
        if match:
            keywords_text = match.group(1).strip()
            return [k.strip() for k in keywords_text.split(',')]
        
        return []
    
    def process(self, df):
        """
        Process PFSI data to categorize tattoos.
        
        Args:
            df: DataFrame with PFSI data
            
        Returns:
            DataFrame with processed tattoos
        """
        print(f"Loaded DataFrame with shape: {df.shape}")
        
        # Filter for rows with tattoos (exclude 'No presenta')
        tattoo_df = df[~df['Tatuajes'].isin(NO_TATTOO_TERMS)].copy()
        tattoo_df = tattoo_df[tattoo_df['Tatuajes'].notna()]
        print(f"Found {len(tattoo_df)} entries with tattoos")
        
        all_tattoos = []
        
        # Process each tattoo entry
        for _, row in tattoo_df.iterrows():
            person_id = row['ID']
            description = row['Tatuajes']
            
            if pd.isna(description):
                continue
            
            # Extract PALABRAS CLAVE if present in the description
            palabras_from_desc = self.parse_palabras_clave(description)
            
            # Clean description by removing PALABRAS CLAVE part
            cleaned_desc = re.sub(
                r'PALABRAS CLAVE:.*$', '', description, flags=re.IGNORECASE
            ).strip()
            
            # Split description into individual tattoos
            individual_tattoos = self.split_tattoos(cleaned_desc)
            
            for tattoo in individual_tattoos:
                # Skip very short descriptions
                if len(tattoo) < 3:
                    continue
                
                # Extract information
                categories, keywords = self.categorize_keywords(tattoo)
                
                # If we found keywords in the description, use those
                if palabras_from_desc:
                    categories = palabras_from_desc
                    keywords = []
                
                location = self.extract_location(tattoo)
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
            output_path = Config.PFSI_TATTOOS
        
        df.to_csv(output_path, index=False)
        print(f"Results saved to {output_path}")
        
        return output_path


def main():
    """Main entry point for PFSI categorization."""
    categorizer = PFSICategorizer()
    return categorizer.run()


if __name__ == "__main__":
    main()

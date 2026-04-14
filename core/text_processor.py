"""
Cross Tattoos Standalone - Text Processor

Unified text preprocessing functions.
Consolidated from multiple files that had duplicated preprocess_text functions.
"""

import re
import pandas as pd


class TextProcessor:
    """Text preprocessing utilities for tattoo descriptions."""
    
    @staticmethod
    def preprocess_text(text):
        """
        Clean and standardize text for comparison.
        
        Args:
            text: Input text to preprocess
            
        Returns:
            Cleaned, lowercase, normalized text
        """
        if not isinstance(text, str):
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation (keep only alphanumeric and spaces)
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    @staticmethod
    def normalize_quotes(text):
        """Normalize different types of quotes to standard double quotes."""
        if not isinstance(text, str):
            return ""
        
        # Replace curly/smart quotes with straight quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        return text
    
    @staticmethod
    def extract_text_in_quotes(text):
        """
        Extract text inside quotes from description.
        
        Args:
            text: Input text that may contain quoted content
            
        Returns:
            Comma-separated string of all quoted content
        """
        if pd.isna(text) or not isinstance(text, str):
            return ""
        
        # Normalize quotes first
        text = TextProcessor.normalize_quotes(text)
        
        # Find all text inside quotes (either "" or "")
        matches = re.findall(r'["\"]([^\"\"]+)["\"]', text)
        
        return ', '.join(matches) if matches else ""
    
    @staticmethod
    def clean_html(raw_html):
        """
        Clean HTML content from web scraping.
        
        Args:
            raw_html: Raw HTML string
            
        Returns:
            Cleaned text with preserved structure
        """
        import html
        
        # Decode Unicode escape sequences and HTML entities
        clean_text = raw_html.encode().decode('unicode_escape')
        clean_text = html.unescape(clean_text)
        
        # Remove unnecessary escape characters
        clean_text = clean_text.replace('\\/', '/')
        
        # Remove new lines and tabs
        clean_text = re.sub(r'\r\n|\t', '', clean_text)
        
        # Remove extra spaces between tags
        clean_text = re.sub(r'>\s+<', '><', clean_text)
        
        return clean_text
    
    @staticmethod
    def prepare_tattoo_features(df, text_columns=None):
        """
        Prepare tattoo dataframe by cleaning text columns.
        
        Args:
            df: DataFrame with tattoo data
            text_columns: List of columns to clean. 
                         Default: ['descripcion_tattoo', 'ubicacion', 'texto_extraido', 
                                   'categorias', 'palabras_clave']
        
        Returns:
            DataFrame with cleaned and prepared text columns
        """
        if text_columns is None:
            text_columns = ['descripcion_tattoo', 'ubicacion', 'texto_extraido', 
                           'categorias', 'palabras_clave']
        
        df = df.copy()
        
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].fillna('')
                if col in ['descripcion_tattoo', 'ubicacion']:
                    df[col] = df[col].str.lower()
        
        return df
    
    @staticmethod
    def create_combined_features(df, feature_columns=None):
        """
        Create a combined feature column from multiple text columns.
        
        Args:
            df: DataFrame with tattoo data
            feature_columns: List of columns to combine.
                            Default: ['descripcion_tattoo', 'ubicacion', 'texto_extraido',
                                     'categorias', 'palabras_clave']
        
        Returns:
            DataFrame with new 'combined_features' column
        """
        if feature_columns is None:
            feature_columns = ['descripcion_tattoo', 'ubicacion', 'texto_extraido',
                              'categorias', 'palabras_clave']
        
        df = df.copy()
        
        # Ensure all columns exist and are strings
        for col in feature_columns:
            if col not in df.columns:
                df[col] = ''
            df[col] = df[col].fillna('').astype(str)
        
        # Combine features
        df['combined_features'] = df[feature_columns].apply(
            lambda x: ' '.join(x), axis=1
        )
        
        # Preprocess combined features
        df['combined_features'] = df['combined_features'].apply(
            TextProcessor.preprocess_text
        )
        
        return df

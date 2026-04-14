"""
Cross Tattoos Standalone - Base Categorizer

Abstract base class for tattoo categorizers.
"""

from abc import ABC, abstractmethod
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.constants import BODY_LOCATIONS, LATERALITY, TATTOO_CATEGORIES


class BaseCategorizer(ABC):
    """Abstract base class for tattoo categorizers."""
    
    def __init__(self):
        self.body_locations = BODY_LOCATIONS
        self.laterality = LATERALITY
        self.categories = TATTOO_CATEGORIES
    
    @abstractmethod
    def load_data(self):
        """Load source data. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def process(self, df):
        """Process the data. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def save_results(self, df, output_path):
        """Save processed results. Must be implemented by subclasses."""
        pass
    
    def categorize_keywords(self, tattoo_description):
        """
        Categorize tattoo description based on keywords.
        
        Args:
            tattoo_description: Text description of the tattoo
            
        Returns:
            Tuple of (categories, triggering_fragments)
        """
        if pd.isna(tattoo_description):
            return [], []
        
        categories = []
        triggering_fragments = []
        
        # Check each category of keywords
        for category, terms in self.categories.items():
            matched_terms = [
                term for term in terms 
                if term.lower() in tattoo_description.lower()
            ]
            if matched_terms:
                categories.append(category)
                triggering_fragments.append(', '.join(matched_terms))
        
        return categories, triggering_fragments
    
    def extract_location(self, description):
        """
        Extract body locations from tattoo descriptions.
        
        Args:
            description: Text description that may contain body locations
            
        Returns:
            Comma-separated string of found locations with laterality
        """
        if pd.isna(description):
            return ""
        
        found_locations = []
        description_upper = description.upper()
        
        for loc in self.body_locations:
            if loc in description_upper:
                # Check for laterality near the location
                position = description_upper.find(loc)
                context = description_upper[
                    max(0, position-10):min(len(description_upper), position+25)
                ]
                side = ""
                for lat in self.laterality:
                    if lat in context:
                        side = lat
                        break
                
                complete_loc = f"{loc} {side}".strip()
                found_locations.append(complete_loc)
        
        return ', '.join(found_locations)
    
    def run(self):
        """Execute the complete categorization pipeline."""
        print(f"Starting {self.__class__.__name__}...")
        
        df = self.load_data()
        if df is None:
            print("Error: Could not load data")
            return None
        
        result_df = self.process(df)
        if result_df is None or len(result_df) == 0:
            print("Error: No results to save")
            return None
        
        output_path = self.save_results(result_df)
        print(f"Completed. Results saved to {output_path}")
        
        return result_df

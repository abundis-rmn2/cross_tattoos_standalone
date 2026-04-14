"""
Cross Tattoos Standalone - Person Matcher

Match missing persons (REPD) with unidentified bodies (PFSI).
Forked from: cross_persons/crossPersons.py
"""

import pandas as pd
import re
from datetime import datetime
from difflib import SequenceMatcher
from tqdm import tqdm
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import Config
from core.data_loader import DataLoader


class PersonMatcher:
    """Match missing persons with unidentified bodies based on demographic criteria."""
    
    def __init__(self):
        self.name_threshold = Config.NAME_SIMILARITY_THRESHOLD
        self.age_tolerance = Config.AGE_TOLERANCE
    
    def match_missing_persons_with_bodies(self, missing_df=None, bodies_df=None):
        """
        Find potential matches between missing persons and unidentified bodies.
        
        Args:
            missing_df: DataFrame with missing persons (REPD). If None, loads from config.
            bodies_df: DataFrame with unidentified bodies (PFSI). If None, loads from config.
            
        Returns:
            DataFrame with potential matches sorted by score
        """
        # Load data if not provided
        if missing_df is None:
            missing_df = DataLoader.load_repd_cedulas()
        if bodies_df is None:
            bodies_df = DataLoader.load_pfsi_raw()
        
        # Filter out records where people have been found alive
        missing_filtered = missing_df[
            missing_df['condicion_localizacion'] != 'CON VIDA'
        ].copy()
        
        # Convert date columns to datetime format
        missing_filtered['fecha_desaparicion'] = pd.to_datetime(
            missing_filtered['fecha_desaparicion']
        )
        bodies_df['Fecha_Ingreso'] = pd.to_datetime(bodies_df['Fecha_Ingreso'])
        
        matches = []
        
        # For each missing person
        for _, missing in tqdm(
            missing_filtered.iterrows(), 
            total=missing_filtered.shape[0], 
            desc="Processing missing persons"
        ):
            # For each unidentified body
            for _, body in bodies_df.iterrows():
                score = 0
                match_reasons = []
                
                # MANDATORY: Check if disappearance date is before forensic intake
                if missing['fecha_desaparicion'] >= body['Fecha_Ingreso']:
                    continue
                
                # MANDATORY: Check if sex matches
                if missing['sexo'].upper() != body['Sexo'].upper():
                    continue
                
                # Check age similarity
                missing_age = missing['edad_momento_desaparicion']
                body_age = body['Edad']
                
                if isinstance(body_age, str) and "-" in body_age:
                    # Handle age range format (e.g., "66-70 años")
                    age_range = re.findall(r'(\d+)-(\d+)', body_age)
                    if age_range:
                        min_age, max_age = map(int, age_range[0])
                        if min_age - self.age_tolerance <= missing_age <= max_age + self.age_tolerance:
                            score += 1
                            match_reasons.append("Age within range")
                
                # Name similarity check (only if body's name isn't just "PFSI")
                body_name = body['Probable_nombre']
                missing_name = missing['nombre_completo']
                
                if body_name and "PFSI" not in str(body_name):
                    name_similarity = SequenceMatcher(
                        None, 
                        str(missing_name).upper(), 
                        str(body_name).upper()
                    ).ratio()
                    
                    if name_similarity > self.name_threshold:
                        score += name_similarity * 2  # Weight name similarity higher
                        match_reasons.append(f"Name similarity: {name_similarity:.2f}")
                
                # Add location match bonus
                if str(missing['municipio']).upper() in str(body['Delegacion_IJCF']).upper():
                    score += 0.5
                    match_reasons.append("Same municipality")
                
                # Calculate days between disappearance and body discovery
                days_between = (body['Fecha_Ingreso'] - missing['fecha_desaparicion']).days
                
                # Add to potential matches if score > 0
                if score > 0:
                    matches.append({
                        'missing_id': missing['id_cedula_busqueda'],
                        'missing_name': missing_name,
                        'missing_age': missing_age,
                        'missing_date': missing['fecha_desaparicion'].strftime('%Y-%m-%d'),
                        'missing_location': missing['municipio'],
                        'body_id': body['ID'],
                        'body_name': body_name,
                        'body_age': body_age,
                        'body_date': body['Fecha_Ingreso'].strftime('%Y-%m-%d'),
                        'body_location': body['Delegacion_IJCF'],
                        'days_between': days_between,
                        'score': score,
                        'match_reasons': ", ".join(match_reasons)
                    })
        
        # Convert to DataFrame and sort by score
        results_df = pd.DataFrame(matches).sort_values('score', ascending=False)
        return results_df
    
    def run(self):
        """Execute the person matching pipeline."""
        print("Starting person matching...")
        results = self.match_missing_persons_with_bodies()
        
        print(f"Found {len(results)} potential matches")
        
        if not results.empty:
            print(results.head(10))
            
            # Save results
            Config.ensure_dirs()
            output_path = Config.PERSON_MATCHES
            results.to_csv(output_path, index=False)
            print(f"Results saved to {output_path}")
        
        return results


def match_missing_persons_with_bodies():
    """Main entry point for person matching."""
    matcher = PersonMatcher()
    return matcher.match_missing_persons_with_bodies()


def main():
    """Main entry point."""
    matcher = PersonMatcher()
    return matcher.run()


if __name__ == "__main__":
    main()

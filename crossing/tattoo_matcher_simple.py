"""
Cross Tattoos Standalone - Simple Tattoo Matcher

Simple tattoo matching using TF-IDF similarity across all records.
Forked from: cross_tattoos/crossTattoo.py
"""

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import time
from tqdm import tqdm
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import Config
from core.data_loader import DataLoader
from core.text_processor import TextProcessor


class SimpleTattooMatcher:
    """
    Simple tattoo matching using TF-IDF similarity.
    Compares all PFSI tattoos against all REPD tattoos.
    """
    
    def __init__(self, use_llm=False):
        """
        Initialize matcher.
        
        Args:
            use_llm: If True, use LLM-categorized datasets. If False, use rule-based.
        """
        self.use_llm = use_llm
        self.threshold = Config.SIMILARITY_THRESHOLD
        self.text_weight = Config.TEXT_WEIGHT
        self.location_weight = Config.LOCATION_WEIGHT
        self.exact_match_weight = Config.EXACT_MATCH_WEIGHT
    
    def load_data(self, sample_size=None):
        """
        Load and prepare tattoo datasets.
        
        Args:
            sample_size: Optional tuple (pfsi_size, repd_size) for sampling.
                        If None, uses all data.
        
        Returns:
            Tuple of (pfsi_df, repd_df)
        """
        dataset_type = "LLM" if self.use_llm else "rule-based"
        print(f"Loading PFSI dataset ({dataset_type})...")
        pfsi_df = DataLoader.load_pfsi_tattoos(use_llm=self.use_llm)
        
        print(f"Loading REPD dataset ({dataset_type})...")
        repd_df = DataLoader.load_repd_tattoos(use_llm=self.use_llm)
        
        # Optional sampling for testing
        if sample_size:
            pfsi_size, repd_size = sample_size
            if pfsi_size and len(pfsi_df) > pfsi_size:
                pfsi_df = pfsi_df.sample(pfsi_size, random_state=42)
            if repd_size and len(repd_df) > repd_size:
                repd_df = repd_df.sample(repd_size, random_state=42)
        
        print("Cleaning and preparing text columns...")
        pfsi_df = TextProcessor.prepare_tattoo_features(pfsi_df)
        repd_df = TextProcessor.prepare_tattoo_features(repd_df)
        
        return pfsi_df, repd_df
    
    def calculate_similarity_scores(self, pfsi_df, repd_df):
        """
        Calculate similarity scores between tattoos using multiple features.
        
        Args:
            pfsi_df: DataFrame with PFSI tattoos
            repd_df: DataFrame with REPD tattoos
            
        Returns:
            DataFrame with matches above threshold
        """
        start_time = time.time()
        results = []
        
        print("Creating combined feature text for each tattoo...")
        pfsi_df = TextProcessor.create_combined_features(pfsi_df)
        repd_df = TextProcessor.create_combined_features(repd_df)
        
        # Create TF-IDF vectors
        print("Creating TF-IDF vectors for combined features...")
        vectorizer = TfidfVectorizer(min_df=1)
        all_features = list(pfsi_df['combined_features']) + list(repd_df['combined_features'])
        vectorizer.fit(all_features)
        
        print(f"Vocabulary size: {len(vectorizer.vocabulary_)}")
        pfsi_vectors = vectorizer.transform(pfsi_df['combined_features'])
        repd_vectors = vectorizer.transform(repd_df['combined_features'])
        
        # Location similarity
        print("Creating TF-IDF vectors for location features...")
        location_vectorizer = TfidfVectorizer(min_df=1)
        all_locations = list(pfsi_df['ubicacion'].fillna('')) + list(repd_df['ubicacion'].fillna(''))
        location_vectorizer.fit(all_locations)
        
        print(f"Location vocabulary size: {len(location_vectorizer.vocabulary_)}")
        pfsi_loc_vectors = location_vectorizer.transform(pfsi_df['ubicacion'].fillna(''))
        repd_loc_vectors = location_vectorizer.transform(repd_df['ubicacion'].fillna(''))
        
        # Calculate similarities for all pairs
        total_comparisons = len(pfsi_df) * len(repd_df)
        print(f"Calculating similarities between {len(pfsi_df)} PFSI and {len(repd_df)} REPD tattoos...")
        print(f"Total comparisons to compute: {total_comparisons}")
        
        matches_count = 0
        pbar = tqdm(total=len(pfsi_df), desc="Processing PFSI records")
        
        for i, pfsi_row in enumerate(pfsi_df.itertuples()):
            pfsi_vector = pfsi_vectors[i]
            pfsi_loc_vector = pfsi_loc_vectors[i]
            
            for j, repd_row in enumerate(repd_df.itertuples()):
                repd_vector = repd_vectors[j]
                repd_loc_vector = repd_loc_vectors[j]
                
                # Calculate similarities
                text_similarity = cosine_similarity(pfsi_vector, repd_vector)[0][0]
                location_similarity = cosine_similarity(pfsi_loc_vector, repd_loc_vector)[0][0]
                
                # Calculate exact text match
                text_match = 0
                pfsi_text = getattr(pfsi_row, 'texto_extraido', '')
                repd_text = getattr(repd_row, 'texto_extraido', '')
                if pfsi_text and repd_text:
                    if str(pfsi_text).lower() == str(repd_text).lower():
                        text_match = 1
                
                # Combined similarity score (weighted)
                combined_score = (
                    self.text_weight * text_similarity + 
                    self.location_weight * location_similarity + 
                    self.exact_match_weight * text_match
                )
                
                if combined_score > self.threshold:
                    matches_count += 1
                    results.append({
                        'pfsi_id': pfsi_row.id_persona,
                        'repd_id': repd_row.id_persona,
                        'pfsi_description': pfsi_row.descripcion_tattoo,
                        'repd_description': repd_row.descripcion_tattoo,
                        'pfsi_location': pfsi_row.ubicacion,
                        'repd_location': repd_row.ubicacion,
                        'text_similarity': round(text_similarity, 3),
                        'location_similarity': round(location_similarity, 3),
                        'text_match': text_match,
                        'similarity': round(combined_score, 3)
                    })
            
            pbar.update(1)
            
            if i > 0 and i % 100 == 0:
                elapsed = time.time() - start_time
                remaining = (elapsed / (i + 1)) * (len(pfsi_df) - i - 1)
                print(f"\nProcessed {i+1}/{len(pfsi_df)} PFSI records. Found {matches_count} matches so far.")
                print(f"Elapsed: {elapsed:.1f}s, Estimated remaining: {remaining:.1f}s")
        
        pbar.close()
        
        processing_time = time.time() - start_time
        print(f"\nSimilarity calculation completed in {processing_time:.1f} seconds")
        print(f"Found {matches_count} matches above threshold ({self.threshold})")
        
        result_df = pd.DataFrame(results).sort_values('similarity', ascending=False)
        return result_df
    
    def analyze_matches(self, matches_df):
        """
        Analyze and output potential tattoo matches.
        
        Args:
            matches_df: DataFrame with tattoo matches
            
        Returns:
            DataFrame with person-level aggregation
        """
        print(f"Found {len(matches_df)} potential matches above threshold.")
        
        if len(matches_df) == 0:
            return pd.DataFrame()
        
        # Group by person pairs
        print("Grouping matches by person pairs...")
        person_pairs = matches_df.groupby(['pfsi_id', 'repd_id']).agg({
            'similarity': ['count', 'mean', 'max']
        })
        
        person_pairs.columns = ['match_count', 'avg_similarity', 'max_similarity']
        person_pairs = person_pairs.sort_values(
            ['match_count', 'avg_similarity'], ascending=False
        )
        
        print(f"\nFound {len(person_pairs)} unique person pairs with at least one matching tattoo")
        pairs_with_multiple = person_pairs[person_pairs['match_count'] > 1]
        print(f"Found {len(pairs_with_multiple)} person pairs with multiple tattoo matches")
        
        print("\nTop person matches (multiple tattoo matches):")
        print(person_pairs.head(10))
        
        print("\nTop individual tattoo matches:")
        print(matches_df.head(20))
        
        return person_pairs
    
    def run(self, sample_size=None):
        """
        Execute the complete tattoo matching pipeline.
        
        Args:
            sample_size: Optional tuple (pfsi_size, repd_size) for sampling
            
        Returns:
            Tuple of (matches_df, person_matches)
        """
        start_time = time.time()
        print("Starting tattoo matching process...")
        
        pfsi_df, repd_df = self.load_data(sample_size)
        print(f"Loaded {len(pfsi_df)} PFSI tattoos and {len(repd_df)} REPD tattoos")
        
        # Print sample data
        print("\nSample PFSI data:")
        print(pfsi_df[['id_persona', 'descripcion_tattoo', 'ubicacion']].head(3))
        print("\nSample REPD data:")
        print(repd_df[['id_persona', 'descripcion_tattoo', 'ubicacion']].head(3))
        
        matches_df = self.calculate_similarity_scores(pfsi_df, repd_df)
        person_matches = self.analyze_matches(matches_df)
        
        # Save results
        Config.ensure_dirs()
        print("Saving results to CSV files...")
        matches_df.to_csv(Config.TATTOO_MATCHES, index=False)
        
        if not person_matches.empty:
            person_matches.to_csv(
                Config.CROSS_EXAMPLES_DIR / 'person_matches_tattoo.csv'
            )
        
        total_time = time.time() - start_time
        print(f"\nTotal processing time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
        print(f"Results saved to {Config.TATTOO_MATCHES}")
        
        return matches_df, person_matches


def main(sample_size=None):
    """Main entry point."""
    matcher = SimpleTattooMatcher()
    return matcher.run(sample_size)


if __name__ == "__main__":
    main()

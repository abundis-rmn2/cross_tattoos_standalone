"""
Cross Tattoos Standalone - Strict Tattoo Matcher

Strict tattoo matching that only compares tattoos between pre-matched person pairs.
Forked from: cross_tattoos/cross_tattoo_prevlist_strict.py
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
from core.constants import ANATOMICAL_PROXIMITY


class StrictTattooMatcher:
    """
    Strict tattoo matching that only compares tattoos between 
    pre-matched person pairs (from PersonMatcher results).
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
        self.category_weight = Config.CATEGORY_WEIGHT
        self.keyword_weight = Config.KEYWORD_WEIGHT
        self.exact_match_weight = Config.EXACT_MATCH_WEIGHT
    
    def load_data(self):
        """
        Load tattoo datasets and the list of probable person matches.
        
        Returns:
            Tuple of (pfsi_df, repd_df, probable_cases_df)
        """
        dataset_type = "LLM" if self.use_llm else "rule-based"
        print(f"Loading PFSI dataset ({dataset_type})...")
        pfsi_df = DataLoader.load_pfsi_tattoos(use_llm=self.use_llm)
        
        print(f"Loading REPD dataset ({dataset_type})...")
        repd_df = DataLoader.load_repd_tattoos(use_llm=self.use_llm)
        
        print("Loading probable cases dataset...")
        probable_cases_df = DataLoader.load_person_matches()
        
        print("Cleaning and preparing text columns...")
        pfsi_df = TextProcessor.prepare_tattoo_features(pfsi_df)
        repd_df = TextProcessor.prepare_tattoo_features(repd_df)
        
        return pfsi_df, repd_df, probable_cases_df

    def get_anatomical_similarity(self, loc1, loc2):
        """Calculate similarity based on anatomical proximity."""
        if not loc1 or not loc2:
            return 0.0
        
        loc1 = str(loc1).upper()
        loc2 = str(loc2).upper()
        
        if loc1 == loc2:
            return 1.0
            
        # Check proximity groups
        for base, neighbors in ANATOMICAL_PROXIMITY.items():
            if (loc1 == base and loc2 in neighbors) or (loc2 == base and loc1 in neighbors):
                return 0.8
            if loc1 in neighbors and loc2 in neighbors:
                return 0.6
                
        return 0.0

    def get_category_similarity(self, cat1, cat2):
        """Calculate similarity between category lists."""
        if not cat1 or not cat2:
            return 0.0
            
        set1 = set(str(cat1).upper().replace(',', ' ').split())
        set2 = set(str(cat2).upper().replace(',', ' ').split())
        
        if not set1 or not set2:
            return 0.0
            
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        
        return len(intersection) / len(union) if union else 0.0

    def get_keyword_similarity(self, kw1, kw2):
        """Calculate similarity between keyword lists."""
        if not kw1 or not kw2:
            return 0.0
            
        set1 = set(str(kw1).lower().replace(',', ' ').split())
        set2 = set(str(kw2).lower().replace(',', ' ').split())
        
        if not set1 or not set2:
            return 0.0
            
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def calculate_similarity_scores_strict(self, pfsi_df, repd_df, probable_cases_df):
        """
        Calculate similarity scores between tattoos only for specific person pairs.
        
        Args:
            pfsi_df: DataFrame with PFSI tattoos
            repd_df: DataFrame with REPD tattoos
            probable_cases_df: DataFrame with person pairs to compare
            
        Returns:
            DataFrame with matches above threshold
        """
        start_time = time.time()
        results = []
        
        # Clear previous results if any
        import os
        output_path = Config.TATTOO_MATCHES_STRICT
        if output_path.exists():
            print(f"Removing previous results at {output_path}")
            os.remove(output_path)
        
        print("Preprocessing tattoo data...")
        pfsi_df = TextProcessor.create_combined_features(pfsi_df)
        repd_df = TextProcessor.create_combined_features(repd_df)
        
        # Create TF-IDF vectors
        print("Creating TF-IDF vectors for combined features...")
        vectorizer = TfidfVectorizer(min_df=1)
        all_features = list(pfsi_df['combined_features']) + list(repd_df['combined_features'])
        vectorizer.fit(all_features)
        print(f"Vocabulary size: {len(vectorizer.vocabulary_)}")
        
        # Create location TF-IDF vectors
        print("Creating TF-IDF vectors for location features...")
        location_vectorizer = TfidfVectorizer(min_df=1)
        all_locations = list(pfsi_df['ubicacion'].fillna('')) + list(repd_df['ubicacion'].fillna(''))
        location_vectorizer.fit(all_locations)
        print(f"Location vocabulary size: {len(location_vectorizer.vocabulary_)}")
        
        # Transform to vectors
        print("Transforming to vectors...")
        pfsi_vectors = vectorizer.transform(pfsi_df['combined_features'])
        repd_vectors = vectorizer.transform(repd_df['combined_features'])
        pfsi_loc_vectors = location_vectorizer.transform(pfsi_df['ubicacion'].fillna(''))
        repd_loc_vectors = location_vectorizer.transform(repd_df['ubicacion'].fillna(''))

        # Pre-normalize vectors for faster dot-product similarity
        from sklearn.preprocessing import normalize
        print("Normalizing vectors...")
        pfsi_vectors_norm = normalize(pfsi_vectors)
        repd_vectors_norm = normalize(repd_vectors)
        pfsi_loc_vectors_norm = normalize(pfsi_loc_vectors)
        repd_loc_vectors_norm = normalize(repd_loc_vectors)

        # Pre-group indices for faster lookup
        print("Grouping tattoos by person ID for faster lookup...")
        pfsi_groups = pfsi_df.reset_index().groupby('id_persona')['index'].apply(list).to_dict()
        repd_groups = repd_df.reset_index().groupby('id_persona')['index'].apply(list).to_dict()
        
        # Convert to records for faster access
        pfsi_data = pfsi_df.to_dict('records')
        repd_data = repd_df.to_dict('records')

        # Process each person pair from probable_cases_df
        print(f"Processing {len(probable_cases_df)} person pairs...")
        matches_count = 0
        pbar = tqdm(total=len(probable_cases_df), desc="Processing person pairs")
        
        for i, pair in enumerate(probable_cases_df.itertuples()):
            body_id = pair.body_id
            missing_id = pair.missing_id
            
            # Get indices for this specific person pair
            body_idx_list = pfsi_groups.get(body_id, [])
            missing_idx_list = repd_groups.get(missing_id, [])
            
            if not body_idx_list or not missing_idx_list:
                pbar.update(1)
                continue
            
            pair_matches = 0
            
            # Compare all tattoos between this person pair
            for bi in body_idx_list:
                body_tattoo = pfsi_data[bi]
                body_vector = pfsi_vectors_norm[bi]
                body_loc_vector = pfsi_loc_vectors_norm[bi]
                
                for mi in missing_idx_list:
                    missing_tattoo = repd_data[mi]
                    missing_vector = repd_vectors_norm[mi]
                    missing_loc_vector = repd_loc_vectors_norm[mi]
                    
                    # 1. TF-IDF Text Similarity
                    text_similarity = float(body_vector.dot(missing_vector.T)[0, 0])
                    
                    # 2. Anatomical Location Similarity (Mixed logic)
                    tf_idf_loc_sim = float(body_loc_vector.dot(missing_loc_vector.T)[0, 0])
                    anatomical_sim = self.get_anatomical_similarity(
                        body_tattoo.get('ubicacion', ''), 
                        missing_tattoo.get('ubicacion', '')
                    )
                    location_similarity = max(tf_idf_loc_sim, anatomical_sim)
                    
                    # 3. Category Similarity
                    category_similarity = self.get_category_similarity(
                        body_tattoo.get('categorias', ''),
                        missing_tattoo.get('categorias', '')
                    )
                    
                    # 4. Keyword Similarity
                    keyword_similarity = self.get_keyword_similarity(
                        body_tattoo.get('palabras_clave', ''),
                        missing_tattoo.get('palabras_clave', '')
                    )
                    
                    # 5. Exact Text Match
                    text_match = 0
                    body_text = body_tattoo.get('texto_extraido', '')
                    missing_text = missing_tattoo.get('texto_extraido', '')
                    if body_text and missing_text:
                        if str(body_text).lower() == str(missing_text).lower():
                            text_match = 1
                    
                    # Refined Combined Similarity Score
                    combined_score = (
                        self.text_weight * text_similarity + 
                        self.location_weight * location_similarity + 
                        self.category_weight * category_similarity +
                        self.keyword_weight * keyword_similarity +
                        self.exact_match_weight * text_match
                    )
                    
                    if combined_score > self.threshold:
                        pair_matches += 1
                        matches_count += 1
                        
                        match_entry = {
                            'pfsi_id': body_id,
                            'repd_id': missing_id,
                            'pfsi_description': body_tattoo.get('descripcion_tattoo', ''),
                            'repd_description': missing_tattoo.get('descripcion_tattoo', ''),
                            'pfsi_location': body_tattoo.get('ubicacion', ''),
                            'repd_location': missing_tattoo.get('ubicacion', ''),
                            'text_similarity': round(text_similarity, 3),
                            'location_similarity': round(location_similarity, 3),
                            'category_similarity': round(category_similarity, 3),
                            'keyword_similarity': round(keyword_similarity, 3),
                            'text_match': text_match,
                            'similarity': round(float(combined_score), 3),
                            'missing_name': pair.missing_name,
                            'missing_age': pair.missing_age,
                            'missing_location': pair.missing_location,
                            'body_name': pair.body_name,
                            'body_age': pair.body_age,
                            'body_location': pair.body_location
                        }
                        results.append(match_entry)
                        
                        # Live save to CSV
                        import os
                        output_path = Config.TATTOO_MATCHES_STRICT
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        pd.DataFrame([match_entry]).to_csv(
                            output_path, 
                            mode='a', 
                            index=False, 
                            header=not os.path.exists(output_path)
                        )
            
            # Display sample output for first few records
            if i < 3 and pair_matches > 0:
                print(f"\nSample match for person pair (Body: {body_id}, Missing: {missing_id}):")
                sample = results[-1]
                print(f"  Body tattoo: '{sample['pfsi_description']}' at {sample['pfsi_location']}")
                print(f"  Missing tattoo: '{sample['repd_description']}' at {sample['repd_location']}")
                print(f"  Scores: text={sample['text_similarity']}, location={sample['location_similarity']}, "
                      f"exact_match={sample['text_match']}, combined={sample['similarity']}")
            
            pbar.update(1)
            
            if (i+1) % 100 == 0:
                elapsed = time.time() - start_time
                remaining = (elapsed / (i + 1)) * (len(probable_cases_df) - i - 1)
                print(f"\nProcessed {i+1}/{len(probable_cases_df)} person pairs. Found {matches_count} matches so far.")
                print(f"Elapsed: {elapsed:.1f}s, Estimated remaining: {remaining:.1f}s")
        
        pbar.close()
        
        processing_time = time.time() - start_time
        print(f"\nSimilarity calculation completed in {processing_time:.1f} seconds")
        print(f"Found {matches_count} matches above threshold ({self.threshold})")
        
        if results:
            result_df = pd.DataFrame(results).sort_values('similarity', ascending=False)
        else:
            result_df = pd.DataFrame(results)
        
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
            print("No matches found.")
            return pd.DataFrame()
        
        if 'pfsi_id' in matches_df.columns and 'repd_id' in matches_df.columns:
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
        else:
            print("No matches found with 'pfsi_id' and 'repd_id' columns.")
            return pd.DataFrame()
    
    def run(self, sample_size=None):
        """
        Execute the strict tattoo matching pipeline.
        
        Args:
           sample_size: Optional number of person pairs to sample from probable_cases_df.
                        If None, uses all data.
        """
        start_time = time.time()
        print(f"Starting STRICT tattoo matching process (only comparing linked person pairs, sample={sample_size})...")
        
        pfsi_df, repd_df, probable_cases_df = self.load_data()
        
        if sample_size and len(probable_cases_df) > sample_size:
            print(f"Taking top {sample_size} person pairs from {len(probable_cases_df)} total...")
            probable_cases_df = probable_cases_df.head(sample_size)
            
        print(f"Loaded {len(pfsi_df)} PFSI tattoos, {len(repd_df)} REPD tattoos, "
              f"and {len(probable_cases_df)} probable case pairs")
        
        # Print sample data
        print("\nSample PFSI data:")
        print(pfsi_df[['id_persona', 'descripcion_tattoo', 'ubicacion']].head(3))
        print("\nSample REPD data:")
        print(repd_df[['id_persona', 'descripcion_tattoo', 'ubicacion']].head(3))
        print("\nSample probable case pairs:")
        print(probable_cases_df[['missing_id', 'body_id', 'missing_name', 'body_name']].head(3))
        
        # Calculate similarity scores
        matches_df = self.calculate_similarity_scores_strict(pfsi_df, repd_df, probable_cases_df)
        person_matches = self.analyze_matches(matches_df)
        
        # Save results
        Config.ensure_dirs()
        print("Saving results to CSV files...")
        matches_df.to_csv(Config.TATTOO_MATCHES_STRICT, index=False)
        
        if not person_matches.empty:
            person_matches.to_csv(
                Config.CROSS_EXAMPLES_DIR / 'person_matches_strict.csv'
            )
        
        total_time = time.time() - start_time
        print(f"\nTotal processing time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
        print(f"Results saved to {Config.TATTOO_MATCHES_STRICT}")
        
        return matches_df, person_matches


def main():
    """Main entry point."""
    matcher = StrictTattooMatcher()
    return matcher.run()


if __name__ == "__main__":
    main()

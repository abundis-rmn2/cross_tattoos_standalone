"""
Cross Tattoos Standalone - Graph Exporter

Export tattoo matches to GraphML format for network analysis.
Forked from: cross_tattoos/tats_csv_to_graph.py
"""

import csv
import networkx as nx
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import Config
from core.data_loader import DataLoader


class GraphExporter:
    """Export tattoo matches to GraphML format."""
    
    def __init__(self):
        pass
    
    def read_csv(self, filepath):
        """
        Read CSV file and return list of dictionaries.
        
        Args:
            filepath: Path to CSV file
            
        Returns:
            List of row dictionaries
        """
        with open(filepath, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            return [row for row in reader]
    
    def create_graph_from_tattoo_matches(self, tattoo_matches):
        """
        Create a graph only using tattoo matches data.
        
        Args:
            tattoo_matches: List of match dictionaries
            
        Returns:
            NetworkX Graph
        """
        G = nx.Graph()
        
        if tattoo_matches:
            print("Tattoo matches columns:", list(tattoo_matches[0].keys()))
        
        for row in tattoo_matches:
            try:
                pfsi_id = row['pfsi_id']
                repd_id = row['repd_id']
                
                # Add PFSI node if it doesn't exist
                if not G.has_node(f"pfsi_{pfsi_id}"):
                    G.add_node(
                        f"pfsi_{pfsi_id}",
                        type='pfsi',
                        name=row.get('body_name', 'Unknown'),
                        age=row.get('body_age', 'Unknown'),
                        location=row.get('body_location', 'Unknown'),
                        description=row.get('pfsi_description', '')
                    )
                
                # Add REPD node if it doesn't exist
                if not G.has_node(f"repd_{repd_id}"):
                    G.add_node(
                        f"repd_{repd_id}",
                        type='repd',
                        name=row.get('missing_name', 'Unknown'),
                        age=row.get('missing_age', 'Unknown'),
                        location=row.get('missing_location', 'Unknown'),
                        description=row.get('repd_description', '')
                    )
                
                # Add edge with similarity data
                edge_data = {
                    'text_similarity': row.get('text_similarity', ''),
                    'location_similarity': row.get('location_similarity', ''),
                    'text_match': row.get('text_match', ''),
                    'similarity': row.get('similarity', '')
                }
                
                G.add_edge(f"pfsi_{pfsi_id}", f"repd_{repd_id}", **edge_data)
                
                # Process PFSI locations (comma-separated)
                if 'pfsi_location' in row and row['pfsi_location']:
                    pfsi_locations = [loc.strip() for loc in row['pfsi_location'].split(',')]
                    for location in pfsi_locations:
                        if location:
                            location_id = f"loc_{location.replace(' ', '_')}"
                            if not G.has_node(location_id):
                                G.add_node(location_id, type='location', name=location)
                            G.add_edge(f"pfsi_{pfsi_id}", location_id, relationship='located_at')
                
                # Process REPD locations (comma-separated)
                if 'repd_location' in row and row['repd_location']:
                    repd_locations = [loc.strip() for loc in row['repd_location'].split(',')]
                    for location in repd_locations:
                        if location:
                            location_id = f"loc_{location.replace(' ', '_')}"
                            if not G.has_node(location_id):
                                G.add_node(location_id, type='location', name=location)
                            G.add_edge(f"repd_{repd_id}", location_id, relationship='found_at')
                
            except KeyError as e:
                print(f"Error processing row: {e}")
                print(f"Row data: {row}")
                continue
        
        return G
    
    def print_stats(self, G):
        """Print graph statistics."""
        location_nodes = [n for n, attr in G.nodes(data=True) if attr.get('type') == 'location']
        pfsi_nodes = [n for n, attr in G.nodes(data=True) if attr.get('type') == 'pfsi']
        repd_nodes = [n for n, attr in G.nodes(data=True) if attr.get('type') == 'repd']
        
        print(f"Graph created with {G.number_of_nodes()} total nodes:")
        print(f"- {len(pfsi_nodes)} PFSI (unidentified body) nodes")
        print(f"- {len(repd_nodes)} REPD (missing person) nodes")
        print(f"- {len(location_nodes)} location nodes")
        print(f"- {G.number_of_edges()} total edges")
    
    def run(self, strict=True):
        """
        Execute the graph export pipeline.
        
        Args:
            strict: If True, use strict matches. If False, use simple matches.
            
        Returns:
            NetworkX Graph
        """
        try:
            # Read the tattoo matches file
            matches_path = Config.TATTOO_MATCHES_STRICT if strict else Config.TATTOO_MATCHES
            print(f"Reading matches from: {matches_path}")
            tattoo_matches = self.read_csv(matches_path)
            
            # Create graph
            G = self.create_graph_from_tattoo_matches(tattoo_matches)
            
            # Print stats
            self.print_stats(G)
            
            # Ensure output directory exists
            Config.ensure_dirs()
            
            # Write graph to file
            output_file = Config.GRAPH_OUTPUT
            nx.write_graphml(G, output_file)
            print(f"Graph saved successfully to {output_file}")
            
            return G
            
        except FileNotFoundError as e:
            print(f"Error: Matches file not found: {e}")
            return None
        except Exception as e:
            print(f"Error in graph export: {e}")
            import traceback
            traceback.print_exc()
            return None


def main(strict=True):
    """Main entry point."""
    exporter = GraphExporter()
    return exporter.run(strict)


if __name__ == "__main__":
    main()

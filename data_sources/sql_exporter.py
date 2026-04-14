"""
Cross Tattoos Standalone - SQL Exporter

Export database tables to CSV files.
Forked from: utils/sql_to_csv.py
"""

import mysql.connector
import pandas as pd
import logging
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import Config


class SQLExporter:
    """Export MySQL tables to CSV files."""
    
    # Available tables for export
    TABLES = [
        'pfsi_v2_principal',
        'repd_vp_cedulas_principal',
        'repd_vp_cedulas_senas',
        'repd_vp_cedulas_vestimenta'
    ]
    
    def __init__(self):
        self.db_config = Config.get_db_config()
    
    def fetch_table(self, table_name):
        """
        Fetch all records from a database table.
        
        Args:
            table_name: Name of the table to fetch
            
        Returns:
            DataFrame with table contents or None on error
        """
        if table_name not in self.TABLES:
            print(f"Warning: Table '{table_name}' is not in the known tables list")
        
        conn = None
        cursor = None
        
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor(dictionary=True)
            query = f"SELECT * FROM {table_name}"
            cursor.execute(query)
            results = cursor.fetchall()
            df = pd.DataFrame(results)
            print(f"Retrieved {len(df)} records from {table_name}")
            return df
            
        except mysql.connector.Error as e:
            logging.error(f"Error fetching data from database: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()
    
    def export_table(self, table_name, output_path=None):
        """
        Export a database table to CSV file.
        
        Args:
            table_name: Name of the table to export
            output_path: Optional custom output path (default: Config.RAW_DIR)
            
        Returns:
            Path to exported file or None on error
        """
        df = self.fetch_table(table_name)
        
        if df is not None:
            if output_path is None:
                Config.ensure_dirs()
                output_path = Config.RAW_DIR / f"{table_name}.csv"
            
            df.to_csv(output_path, index=False)
            print(f"Data saved to {output_path}")
            return output_path
        
        return None
    
    def export_all(self):
        """
        Export all known tables to CSV files.
        
        Returns:
            Dictionary mapping table names to output paths
        """
        results = {}
        
        for table in self.TABLES:
            try:
                path = self.export_table(table)
                results[table] = path
            except Exception as e:
                print(f"Error exporting {table}: {e}")
                results[table] = None
        
        return results
    
    def export_for_pipeline(self):
        """
        Export the main tables needed for the tattoo matching pipeline.
        Also creates the expected file names in the config.
        
        Returns:
            Dictionary with export results
        """
        Config.ensure_dirs()
        results = {}
        
        # Map table names to their expected config paths
        table_mapping = {
            'pfsi_v2_principal': Config.PFSI_FILE,
            'repd_vp_cedulas_principal': Config.REPD_CEDULAS,
            'repd_vp_cedulas_senas': Config.REPD_SENAS,
            'repd_vp_cedulas_vestimenta': Config.REPD_VESTIMENTA
        }
        
        for table, output_path in table_mapping.items():
            try:
                df = self.fetch_table(table)
                if df is not None:
                    df.to_csv(output_path, index=False)
                    print(f"Exported {table} to {output_path}")
                    results[table] = output_path
                else:
                    results[table] = None
            except Exception as e:
                print(f"Error exporting {table}: {e}")
                results[table] = None
        
        return results


def export_table(table_name):
    """Main entry point for single table export."""
    exporter = SQLExporter()
    return exporter.export_table(table_name)


def export_all():
    """Main entry point for exporting all tables."""
    exporter = SQLExporter()
    return exporter.export_all()


if __name__ == "__main__":
    exporter = SQLExporter()
    exporter.export_for_pipeline()

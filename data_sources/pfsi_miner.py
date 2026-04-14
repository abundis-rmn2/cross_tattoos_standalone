"""
Cross Tattoos Standalone - PFSI Miner

Web scraper for PFSI (Personas Fallecidas Sin Identificar) data.
Forked from: utils/pfsi_mine.py
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import html
import re
import mysql.connector
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import Config
from core.text_processor import TextProcessor


class PFSIMiner:
    """Miner for PFSI data from the Jalisco forensic sciences portal."""
    
    def __init__(self):
        self.url = Config.PFSI_URL
    
    def retrieve_data(self, start_date=None, end_date=None):
        """
        Retrieve PFSI data from the web portal.
        
        Args:
            start_date: Start date in DD/MM/YYYY format (default from config)
            end_date: End date in DD/MM/YYYY format (default from config)
            
        Returns:
            Cleaned HTML content or None if request fails
        """
        start_date = start_date or Config.PFSI_DEFAULT_START_DATE
        end_date = end_date or Config.PFSI_DEFAULT_END_DATE
        
        payload = {
            'inicio': start_date,
            'fin': end_date,
            'sexo': '',
            'tatuajes': '',
            'nocache': '0.6192728608924991',
        }
        
        try:
            response = requests.post(self.url, data=payload)
            
            if response.status_code == 200:
                print("Data retrieved successfully")
                
                # Handle BOM and isolate the HTML content
                json_prefix = '{"datos":"'
                bom = '\ufeff'
                raw_text = response.text
                
                if raw_text.startswith(bom):
                    raw_text = raw_text.lstrip(bom)
                
                if raw_text.startswith(json_prefix):
                    # Remove the prefix and trailing characters
                    html_content = raw_text[len(json_prefix):-2]
                    # Clean the HTML content
                    html_content = TextProcessor.clean_html(html_content)
                    return html_content
                else:
                    print("Unexpected response format.")
                    return None
            else:
                print(f"Request failed with status code {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching PFSI data: {e}")
            return None
    
    def parse_html_to_json(self, html_content):
        """
        Parse HTML table content to JSON structure.
        
        Args:
            html_content: Cleaned HTML string
            
        Returns:
            Dictionary with 'datos' key containing list of entries
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        table = soup.find('table')
        if table is None:
            print("Table not found in the HTML.")
            return {"datos": []}
        
        headers = [th.get_text(strip=True) for th in table.find('thead').find_all('th')]
        
        rows = table.find('tbody').find_all('tr')
        data = []
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) != len(headers):
                continue
            entry = {headers[i]: cells[i].get_text(strip=True) for i in range(len(headers))}
            data.append(entry)
        
        print(f"Parsed {len(data)} entries")
        return {"datos": data}
    
    def insert_entry(self, cursor, entry):
        """Insert a single entry into the database."""
        sql = """
        INSERT INTO pfsi_v2_principal (
            ID, Fecha_Ingreso, Sexo, Probable_nombre, Edad,
            Tatuajes, Indumentarias, Senas_Particulares, Delegacion_IJCF
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            Fecha_Ingreso=VALUES(Fecha_Ingreso),
            Sexo=VALUES(Sexo),
            Probable_nombre=VALUES(Probable_nombre),
            Edad=VALUES(Edad),
            Tatuajes=VALUES(Tatuajes),
            Indumentarias=VALUES(Indumentarias),
            Senas_Particulares=VALUES(Senas_Particulares),
            Delegacion_IJCF=VALUES(Delegacion_IJCF)
        """
        
        # Parse the date
        fecha_ingreso = datetime.strptime(
            entry["Fecha Ingreso"], "%d/%m/%Y"
        ).strftime("%Y-%m-%d")
        
        values = (
            entry["ID"],
            fecha_ingreso,
            entry["Sexo"],
            entry["Probable nombre"],
            entry["Edad"],
            entry["Tatuajes"],
            entry["Indumentarias"],
            entry["Señas Particulares"],
            entry["Delegación IJCF"]
        )
        cursor.execute(sql, values)
    
    def update_database(self, json_response):
        """
        Insert parsed data into MySQL database.
        
        Args:
            json_response: Dictionary with 'datos' key
        """
        db_config = Config.get_db_config()
        
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()
        
        for entry in json_response["datos"]:
            self.insert_entry(cursor, entry)
        
        cnx.commit()
        cursor.close()
        cnx.close()
        
        print(f"Inserted/updated {len(json_response['datos'])} entries to database")
    
    def save_to_csv(self, json_response):
        """
        Save parsed data to CSV file.
        
        Args:
            json_response: Dictionary with 'datos' key
        """
        Config.ensure_dirs()
        
        data = json_response.get("datos", [])
        if not data:
            print("No data to save")
            return
        
        # Normalize column names for CSV
        records = []
        for entry in data:
            records.append({
                'ID': entry.get('ID'),
                'Fecha_Ingreso': entry.get('Fecha Ingreso'),
                'Sexo': entry.get('Sexo'),
                'Probable_nombre': entry.get('Probable nombre'),
                'Edad': entry.get('Edad'),
                'Tatuajes': entry.get('Tatuajes'),
                'Indumentarias': entry.get('Indumentarias'),
                'Senas_Particulares': entry.get('Señas Particulares'),
                'Delegacion_IJCF': entry.get('Delegación IJCF')
            })
        
        df = pd.DataFrame(records)
        df.to_csv(Config.PFSI_FILE, index=False)
        print(f"  ✓ Saved {len(df)} records to {Config.PFSI_FILE}")
    
    def run(self, start_date=None, end_date=None, to_database=False):
        """
        Run the complete mining pipeline.
        
        Args:
            start_date: Start date in DD/MM/YYYY format
            end_date: End date in DD/MM/YYYY format
            to_database: If True, insert into database (default: False)
            
        Returns:
            Parsed JSON data
        """
        raw_response = self.retrieve_data(start_date, end_date)
        
        if raw_response:
            json_response = self.parse_html_to_json(raw_response)
            
            # Always save to CSV
            print("\nSaving to CSV...")
            self.save_to_csv(json_response)
            
            # Optionally insert to database
            if to_database:
                self.update_database(json_response)
            
            return json_response
        
        return None


def main(start_date=None, end_date=None):
    """Main entry point for PFSI mining."""
    miner = PFSIMiner()
    return miner.run(start_date, end_date)


if __name__ == '__main__':
    main()


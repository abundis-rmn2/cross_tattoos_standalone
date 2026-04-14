"""
Cross Tattoos Standalone - REPD Miner

API client for REPD (Registro Estatal de Personas Desaparecidas) data.
Forked from: utils/repd_mine.py
"""

import requests
import mysql.connector
import pandas as pd
import time
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import Config


class REPDMiner:
    """Miner for REPD data from the Jalisco API."""
    
    def __init__(self):
        self.base_url = Config.REPD_API_BASE_URL
        self.default_limit = Config.REPD_DEFAULT_LIMIT
        self.pause_time = Config.REPD_PAUSE_TIME
    
    def fetch_data(self, limit=None, pause_time=None, to_database=True):
        """
        Fetch all data from REPD API by iterating through all pages.
        
        Args:
            limit: Records per page (default from config)
            pause_time: Seconds to wait between API calls (default from config)
            to_database: If True, insert into database
            
        Returns:
            List of all fetched records
        """
        limit = limit or self.default_limit
        pause_time = pause_time or self.pause_time
        
        try:
            # Get initial response to determine total pages
            initial_response = requests.get(f"{self.base_url}?limit={limit}&page=1")
            initial_response.raise_for_status()
            initial_data = initial_response.json()
            
            total_count = initial_data.get("count", 0)
            total_pages = initial_data.get("total_pages", 1)
            
            # Calculate probable total pages
            probable_total_pages = (total_count // limit) + (1 if total_count % limit != 0 else 0)
            
            if probable_total_pages == total_pages:
                print(f"Total pages match: {probable_total_pages}. Proceeding to fetch all pages.")
            else:
                print(f"Warning: Probable total pages ({probable_total_pages}) does not match "
                      f"API's total pages ({total_pages}). Proceeding cautiously.")
            
            all_results = []
            
            # Iterate through all pages
            for page in range(1, total_pages + 1):
                print(f"Fetching page {page}/{total_pages}...")
                response = requests.get(f"{self.base_url}?limit={limit}&page={page}")
                response.raise_for_status()
                page_data = response.json()
                
                results_in_page = page_data.get("results", [])
                all_results.extend(results_in_page)
                
                if to_database and results_in_page:
                    self.insert_data_to_db(results_in_page)
                
                # Pause between requests
                time.sleep(pause_time)
            
            print(f"Total records fetched: {len(all_results)}")
            return all_results
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error: {e}")
            return []
    
    def insert_data_to_db(self, data):
        """
        Insert API data into MySQL database.
        
        Args:
            data: List of record dictionaries
        """
        conn = None
        cursor = None
        
        try:
            db_config = Config.get_db_config()
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            
            for record in data:
                # Insert into repd_vp_cedulas_principal
                principal_query = """
                    INSERT INTO repd_vp_cedulas_principal (
                        id_cedula_busqueda, autorizacion_informacion_publica, condicion_localizacion,
                        nombre_completo, edad_momento_desaparicion, sexo, genero, complexion, estatura,
                        tez, cabello, ojos_color, municipio, estado, fecha_desaparicion,
                        estatus_persona_desaparecida, descripcion_desaparicion, ruta_foto
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        autorizacion_informacion_publica=VALUES(autorizacion_informacion_publica),
                        condicion_localizacion=VALUES(condicion_localizacion),
                        nombre_completo=VALUES(nombre_completo),
                        edad_momento_desaparicion=VALUES(edad_momento_desaparicion),
                        sexo=VALUES(sexo), genero=VALUES(genero),
                        complexion=VALUES(complexion), estatura=VALUES(estatura),
                        tez=VALUES(tez), cabello=VALUES(cabello),
                        ojos_color=VALUES(ojos_color), municipio=VALUES(municipio),
                        estado=VALUES(estado), fecha_desaparicion=VALUES(fecha_desaparicion),
                        estatus_persona_desaparecida=VALUES(estatus_persona_desaparecida),
                        descripcion_desaparicion=VALUES(descripcion_desaparicion),
                        ruta_foto=VALUES(ruta_foto)
                """
                principal_values = (
                    record.get("id_cedula_busqueda"),
                    record.get("autorizacion_informacion_publica"),
                    record.get("condicion_localizacion"),
                    record.get("nombre_completo"),
                    record.get("edad_momento_desaparicion"),
                    record.get("sexo"),
                    record.get("genero"),
                    record.get("complexion"),
                    record.get("estatura"),
                    record.get("tez"),
                    record.get("cabello"),
                    record.get("ojos_color"),
                    record.get("municipio"),
                    record.get("estado"),
                    record.get("fecha_desaparicion"),
                    record.get("estatus_persona_desaparecida"),
                    record.get("descripcion_desaparicion", ""),  # May not exist
                    record.get("ruta_foto")
                )
                cursor.execute(principal_query, principal_values)
                
                # Insert into repd_vp_cedulas_senas
                for sena in record.get("descripcion_sena_particular", []):
                    sena_query = """
                        INSERT INTO repd_vp_cedulas_senas (
                            id, id_cedula_busqueda, especificacion_general, parte_cuerpo, 
                            tipo_sena, descripcion
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            especificacion_general=VALUES(especificacion_general),
                            parte_cuerpo=VALUES(parte_cuerpo),
                            tipo_sena=VALUES(tipo_sena),
                            descripcion=VALUES(descripcion)
                    """
                    sena_values = (
                        sena["id"],
                        sena["id_cedula_busqueda"],
                        sena["especificacion_general"],
                        sena["parte_cuerpo"],
                        sena["tipo_sena"],
                        sena["descripcion"]
                    )
                    cursor.execute(sena_query, sena_values)
                
                # Insert into repd_vp_cedulas_vestimenta
                for vestimenta in record.get("descripcion_vestimenta", []):
                    vestimenta_query = """
                        INSERT INTO repd_vp_cedulas_vestimenta (
                            id, id_cedula_busqueda, clase_prenda, grupo_prenda, prenda, 
                            marca, color, material, talla, tipo, descripcion
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            clase_prenda=VALUES(clase_prenda),
                            grupo_prenda=VALUES(grupo_prenda),
                            prenda=VALUES(prenda),
                            marca=VALUES(marca),
                            color=VALUES(color),
                            material=VALUES(material),
                            talla=VALUES(talla),
                            tipo=VALUES(tipo),
                            descripcion=VALUES(descripcion)
                    """
                    vestimenta_values = (
                        vestimenta["id"],
                        vestimenta["id_cedula_busqueda"],
                        vestimenta["clase_prenda"],
                        vestimenta["grupo_prenda"],
                        vestimenta["prenda"],
                        vestimenta["marca"],
                        vestimenta["color"],
                        vestimenta["material"],
                        vestimenta["talla"],
                        vestimenta["tipo"],
                        vestimenta["descripcion"]
                    )
                    cursor.execute(vestimenta_query, vestimenta_values)
            
            conn.commit()
            print("Data successfully inserted into the database!")
            
        except mysql.connector.Error as e:
            print(f"Error inserting data into database: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()
    
    def save_to_csv(self, data):
        """
        Save fetched data to CSV files.
        
        Args:
            data: List of record dictionaries from API
        """
        Config.ensure_dirs()
        
        # Prepare DataFrames for each table
        principal_records = []
        senas_records = []
        vestimenta_records = []
        
        for record in data:
            # Principal data
            principal_records.append({
                'id_cedula_busqueda': record.get('id_cedula_busqueda'),
                'autorizacion_informacion_publica': record.get('autorizacion_informacion_publica'),
                'condicion_localizacion': record.get('condicion_localizacion'),
                'nombre_completo': record.get('nombre_completo'),
                'edad_momento_desaparicion': record.get('edad_momento_desaparicion'),
                'sexo': record.get('sexo'),
                'genero': record.get('genero'),
                'complexion': record.get('complexion'),
                'estatura': record.get('estatura'),
                'tez': record.get('tez'),
                'cabello': record.get('cabello'),
                'ojos_color': record.get('ojos_color'),
                'municipio': record.get('municipio'),
                'estado': record.get('estado'),
                'fecha_desaparicion': record.get('fecha_desaparicion'),
                'estatus_persona_desaparecida': record.get('estatus_persona_desaparecida'),
                'descripcion_desaparicion': record.get('descripcion_desaparicion', ''),
                'ruta_foto': record.get('ruta_foto')
            })
            
            # Senas particulares
            for sena in record.get('descripcion_sena_particular', []):
                senas_records.append({
                    'id': sena.get('id'),
                    'id_cedula_busqueda': sena.get('id_cedula_busqueda'),
                    'especificacion_general': sena.get('especificacion_general'),
                    'parte_cuerpo': sena.get('parte_cuerpo'),
                    'tipo_sena': sena.get('tipo_sena'),
                    'descripcion': sena.get('descripcion')
                })
            
            # Vestimenta
            for vestimenta in record.get('descripcion_vestimenta', []):
                vestimenta_records.append({
                    'id': vestimenta.get('id'),
                    'id_cedula_busqueda': vestimenta.get('id_cedula_busqueda'),
                    'clase_prenda': vestimenta.get('clase_prenda'),
                    'grupo_prenda': vestimenta.get('grupo_prenda'),
                    'prenda': vestimenta.get('prenda'),
                    'marca': vestimenta.get('marca'),
                    'color': vestimenta.get('color'),
                    'material': vestimenta.get('material'),
                    'talla': vestimenta.get('talla'),
                    'tipo': vestimenta.get('tipo'),
                    'descripcion': vestimenta.get('descripcion')
                })
        
        # Save to CSV
        principal_df = pd.DataFrame(principal_records)
        principal_df.to_csv(Config.REPD_CEDULAS, index=False)
        print(f"  ✓ Saved {len(principal_df)} records to {Config.REPD_CEDULAS}")
        
        senas_df = pd.DataFrame(senas_records)
        senas_df.to_csv(Config.REPD_SENAS, index=False)
        print(f"  ✓ Saved {len(senas_df)} senas to {Config.REPD_SENAS}")
        
        vestimenta_df = pd.DataFrame(vestimenta_records)
        vestimenta_df.to_csv(Config.REPD_VESTIMENTA, index=False)
        print(f"  ✓ Saved {len(vestimenta_df)} vestimenta to {Config.REPD_VESTIMENTA}")
    
    def run(self, limit=None, pause_time=None, to_database=False):
        """
        Run the complete mining pipeline.
        
        Args:
            limit: Records per page
            pause_time: Seconds between API calls
            to_database: If True, insert into database (default: False)
            
        Returns:
            List of all fetched records
        """
        data = self.fetch_data(limit, pause_time, to_database)
        
        if data:
            print("\nSaving to CSV files...")
            self.save_to_csv(data)
        
        return data


def fetch_data(limit=1000, pause_time=2, to_database=False):
    """Main entry point for REPD mining."""
    miner = REPDMiner()
    return miner.run(limit, pause_time, to_database)


if __name__ == "__main__":
    fetch_data(limit=1000, pause_time=2)



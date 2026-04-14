"""
Cross Tattoos Standalone - PFSI Categorizer with LLM

Categoriza tatuajes PFSI usando DeepSeek API para estandarización.
Forked from: ds/cat_tattoo_PFSI.py
"""

import pandas as pd
from pathlib import Path
import sys
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import Config
from core.data_loader import DataLoader
from core.constants import NO_TATTOO_TERMS
from llm.deepseek_client import DeepSeekClient


class PFSICategorizerLLM:
    """
    Categoriza tatuajes PFSI usando DeepSeek API.
    
    Ventajas sobre reglas:
    - Estandariza descripciones inconsistentes
    - Detecta categorías semánticas que las reglas no capturan
    - Separa múltiples tatuajes en una sola descripción
    - Extrae texto literal (nombres, fechas) de forma inteligente
    """
    
    def __init__(self):
        self.client = DeepSeekClient()
        self.batch_size = 10  # Procesar en lotes para evitar rate limits
        self.delay_between_calls = 1  # Segundos entre llamadas API
    
    def load_data(self):
        """Cargar datos PFSI con tatuajes."""
        try:
            df = DataLoader.load_pfsi_raw()
            # Filtrar solo registros con tatuajes
            df = df[~df['Tatuajes'].isin(NO_TATTOO_TERMS)]
            df = df[df['Tatuajes'].notna()]
            df = df[df['Tatuajes'].str.strip() != '']
            return df
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return None
    
    def create_prompt(self, id_persona, tattoo_description):
        """
        Crear prompt para DeepSeek.
        
        El prompt instruye al modelo a:
        1. Separar múltiples tatuajes
        2. Estandarizar ubicaciones corporales
        3. Extraer texto literal
        4. Asignar categorías consistentes
        """
        return f"""
Eres un médico forense experto en tatuajes. Tu tarea es analizar la siguiente descripción de tatuajes y categorizarlos de manera estructurada.

DESCRIPCIÓN ORIGINAL:
"{tattoo_description}"

INSTRUCCIONES:
1. Si hay múltiples tatuajes, sepáralos en registros individuales
2. Para cada tatuaje, extrae:
   - ubicacion: La parte del cuerpo EN MAYÚSCULAS (ej: "BRAZO DERECHO", "ESPALDA ALTA")
   - texto_extraido: Cualquier texto literal, nombre o fecha que aparezca
   - categorias: Una o más de estas categorías separadas por coma:
     RELIGIOSO, ANIMALES, SIMBOLOS, NOMBRES_FECHAS, TRIBAL, NATURALEZA, 
     LETRAS_NUMEROS, CORAZONES, CALAVERAS, OTROS
   - descripcion_estandarizada: Una descripción breve y estandarizada del tatuaje

FORMATO DE RESPUESTA:
Responde SOLO con un arreglo JSON válido, sin explicaciones adicionales:
[
    {{
        "id_persona": "{id_persona}",
        "descripcion_original": "{tattoo_description}",
        "descripcion_tattoo": "descripción individual del tatuaje",
        "ubicacion": "UBICACIÓN EN MAYÚSCULAS",
        "texto_extraido": "texto o vacío si no hay",
        "categorias": "CATEGORIA1, CATEGORIA2",
        "palabras_clave": "palabras clave separadas por coma"
    }}
]
"""
    
    def process_single(self, id_persona, tattoo_description):
        """
        Procesar una sola descripción de tatuaje con DeepSeek.
        
        Returns:
            Lista de diccionarios con tatuajes categorizados
        """
        prompt = self.create_prompt(id_persona, tattoo_description)
        
        try:
            response = self.client.generate(prompt)
            
            if response:
                tattoos = self.client.parse_tattoo_response(response)
                return tattoos
            else:
                print(f"  ⚠️ Sin respuesta para ID {id_persona}")
                return None
                
        except Exception as e:
            print(f"  ✗ Error procesando ID {id_persona}: {e}")
            return None
    
    def process_batch(self, df, start_idx=0, max_records=None):
        """
        Procesar un lote de registros.
        
        Args:
            df: DataFrame con datos PFSI
            start_idx: Índice inicial (para continuar proceso interrumpido)
            max_records: Máximo de registros a procesar (None = todos)
        
        Returns:
            DataFrame con todos los tatuajes categorizados
        """
        all_results = []
        
        records = df.iloc[start_idx:]
        if max_records:
            records = records.head(max_records)
        
        total = len(records)
        processed = 0
        errors = 0
        
        print(f"Procesando {total} registros con LLM...")
        
        for idx, row in records.iterrows():
            id_persona = row['ID']
            description = row['Tatuajes']
            
            print(f"[{processed+1}/{total}] ID: {id_persona}")
            
            result = self.process_single(id_persona, description)
            
            if result:
                all_results.extend(result)
                print(f"  ✓ {len(result)} tatuaje(s) extraído(s)")
            else:
                errors += 1
                # Agregar registro con información básica
                all_results.append({
                    'id_persona': id_persona,
                    'descripcion_original': description,
                    'descripcion_tattoo': description,
                    'ubicacion': '',
                    'texto_extraido': '',
                    'categorias': 'ERROR_PROCESAMIENTO',
                    'palabras_clave': ''
                })
            
            processed += 1
            
            # Delay para respetar rate limits
            time.sleep(self.delay_between_calls)
            
            # Guardar checkpoint cada 50 registros
            if processed % 50 == 0:
                self._save_checkpoint(all_results, processed)
        
        print(f"\nProcesamiento completado:")
        print(f"  - Procesados: {processed}")
        print(f"  - Errores: {errors}")
        print(f"  - Tatuajes extraídos: {len(all_results)}")
        
        return pd.DataFrame(all_results)
    
    def _save_checkpoint(self, results, processed_count):
        """Guardar checkpoint para poder continuar si se interrumpe."""
        checkpoint_path = Config.PROCESSED_DIR / f"checkpoint_pfsi_llm_{processed_count}.csv"
        pd.DataFrame(results).to_csv(checkpoint_path, index=False)
        print(f"  📁 Checkpoint guardado: {checkpoint_path}")
    
    def run(self, max_records=None):
        """
        Ejecutar pipeline completo de categorización con LLM.
        
        Args:
            max_records: Límite de registros a procesar (para testing)
        
        Returns:
            DataFrame con resultados
        """
        print("=" * 60)
        print("PFSI CATEGORIZER - LLM (DeepSeek)")
        print("=" * 60)
        
        # Verificar API key
        if not Config.DEEPSEEK_API_KEY:
            print("✗ Error: DEEPSEEK_API_KEY no configurada")
            print("  Configura la variable en config/.env")
            return None
        
        # Cargar datos
        print("\n[1/3] Cargando datos PFSI...")
        df = self.load_data()
        if df is None or len(df) == 0:
            print("✗ No hay datos para procesar")
            return None
        print(f"  ✓ {len(df)} registros con tatuajes")
        
        # Procesar con LLM
        print("\n[2/3] Procesando con DeepSeek...")
        result_df = self.process_batch(df, max_records=max_records)
        
        # Guardar resultados
        print("\n[3/3] Guardando resultados...")
        Config.ensure_dirs()
        output_path = Config.LLM_PFSI_TATTOOS
        result_df.to_csv(output_path, index=False)
        print(f"  ✓ Guardado en: {output_path}")
        
        return result_df


def main(max_records=None):
    """Punto de entrada principal."""
    categorizer = PFSICategorizerLLM()
    return categorizer.run(max_records)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--max', type=int, default=None, 
                       help='Máximo de registros a procesar')
    args = parser.parse_args()
    main(args.max)

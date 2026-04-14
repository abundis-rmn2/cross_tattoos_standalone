"""
Cross Tattoos Standalone - REPD Categorizer with LLM

Categoriza tatuajes REPD usando DeepSeek API para estandarización.
Forked from: ds/cat_tattoo_REPD.py
"""

import pandas as pd
from pathlib import Path
import sys
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import Config
from core.data_loader import DataLoader
from llm.deepseek_client import DeepSeekClient


class REPDCategorizerLLM:
    """
    Categoriza tatuajes REPD usando DeepSeek API.
    
    Los datos REPD ya vienen con estructura (parte_cuerpo, tipo_sena),
    pero las descripciones son inconsistentes y requieren estandarización.
    """
    
    def __init__(self):
        self.client = DeepSeekClient()
        self.batch_size = 10
        self.delay_between_calls = 1
    
    def load_data(self):
        """Cargar datos REPD (señas particulares)."""
        try:
            df = DataLoader.load_repd_senas()
            # Filtrar solo tatuajes
            if 'tipo_sena' in df.columns:
                df = df[df['tipo_sena'].astype(str).str.upper().str.contains('TATUAJE', na=False)]
            df = df[df['descripcion'].notna()]
            df = df[df['descripcion'].str.strip() != '']
            return df
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return None
    
    def create_prompt(self, id_persona, tattoo_description, body_part=""):
        """
        Crear prompt para DeepSeek.
        
        REPD ya tiene body_part, así que lo usamos como contexto.
        """
        body_context = f"\nUBICACIÓN (del registro): {body_part}" if body_part else ""
        
        return f"""
Eres un médico forense experto en tatuajes. Tu tarea es analizar y estandarizar la siguiente descripción de tatuaje.
{body_context}

DESCRIPCIÓN ORIGINAL:
"{tattoo_description}"

INSTRUCCIONES:
1. Si hay múltiples tatuajes en la descripción, sepáralos
2. Estandariza la ubicación corporal EN MAYÚSCULAS
3. Extrae cualquier texto literal (nombres, fechas, frases)
4. Asigna categorías de esta lista:
   RELIGIOSO, ANIMALES, SIMBOLOS, NOMBRES_FECHAS, TRIBAL, NATURALEZA,
   LETRAS_NUMEROS, CORAZONES, CALAVERAS, OTROS
5. Genera una descripción estandarizada breve

FORMATO DE RESPUESTA:
Responde SOLO con un arreglo JSON válido:
[
    {{
        "id_persona": "{id_persona}",
        "descripcion_original": "{tattoo_description}",
        "descripcion_tattoo": "descripción estandarizada del tatuaje",
        "ubicacion": "UBICACIÓN EN MAYÚSCULAS",
        "texto_extraido": "texto literal encontrado o vacío",
        "categorias": "CATEGORIA1, CATEGORIA2",
        "palabras_clave": "palabras clave separadas por coma"
    }}
]

Si la descripción contiene múltiples tatuajes, devuelve múltiples objetos en el arreglo.
"""
    
    def process_single(self, id_persona, tattoo_description, body_part=""):
        """Procesar una sola descripción con DeepSeek."""
        prompt = self.create_prompt(id_persona, tattoo_description, body_part)
        
        try:
            response = self.client.generate(prompt)
            
            if response:
                tattoos = self.client.parse_tattoo_response(response)
                return tattoos
            else:
                return None
                
        except Exception as e:
            print(f"  ✗ Error procesando ID {id_persona}: {e}")
            return None
    
    def process_batch(self, df, start_idx=0, max_records=None):
        """Procesar lote de registros."""
        all_results = []
        
        records = df.iloc[start_idx:]
        if max_records:
            records = records.head(max_records)
        
        total = len(records)
        processed = 0
        errors = 0
        
        print(f"Procesando {total} registros con LLM...")
        
        for idx, row in records.iterrows():
            id_persona = row.get('id_cedula_busqueda', row.get('id', 'unknown'))
            description = row.get('descripcion', '')
            body_part = row.get('parte_cuerpo', '')
            if pd.isna(body_part):
                body_part = ""
            
            print(f"[{processed+1}/{total}] ID: {id_persona}")
            
            result = self.process_single(id_persona, description, body_part)
            
            if result:
                all_results.extend(result)
                print(f"  ✓ {len(result)} tatuaje(s) extraído(s)")
            else:
                errors += 1
                # Handle possible non-string body_part (like NaN float)
                location = str(body_part).upper() if body_part is not None and not pd.isna(body_part) else ''
                
                all_results.append({
                    'id_persona': id_persona,
                    'descripcion_original': description,
                    'descripcion_tattoo': description,
                    'ubicacion': location,
                    'texto_extraido': '',
                    'categorias': 'ERROR_PROCESAMIENTO',
                    'palabras_clave': ''
                })
            
            processed += 1
            time.sleep(self.delay_between_calls)
            
            if processed % 50 == 0:
                self._save_checkpoint(all_results, processed)
        
        print(f"\nProcesamiento completado:")
        print(f"  - Procesados: {processed}")
        print(f"  - Errores: {errors}")
        print(f"  - Tatuajes extraídos: {len(all_results)}")
        
        return pd.DataFrame(all_results)
    
    def _save_checkpoint(self, results, processed_count):
        """Guardar checkpoint."""
        checkpoint_path = Config.PROCESSED_DIR / f"checkpoint_repd_llm_{processed_count}.csv"
        pd.DataFrame(results).to_csv(checkpoint_path, index=False)
        print(f"  📁 Checkpoint guardado: {checkpoint_path}")
    
    def run(self, max_records=None):
        """Ejecutar pipeline completo."""
        print("=" * 60)
        print("REPD CATEGORIZER - LLM (DeepSeek)")
        print("=" * 60)
        
        if not Config.DEEPSEEK_API_KEY:
            print("✗ Error: DEEPSEEK_API_KEY no configurada")
            print("  Configura la variable en config/.env")
            return None
        
        print("\n[1/3] Cargando datos REPD...")
        df = self.load_data()
        if df is None or len(df) == 0:
            print("✗ No hay datos para procesar")
            return None
        print(f"  ✓ {len(df)} registros con tatuajes")
        
        print("\n[2/3] Procesando con DeepSeek...")
        result_df = self.process_batch(df, max_records=max_records)
        
        print("\n[3/3] Guardando resultados...")
        Config.ensure_dirs()
        output_path = Config.LLM_REPD_TATTOOS
        result_df.to_csv(output_path, index=False)
        print(f"  ✓ Guardado en: {output_path}")
        
        return result_df


def main(max_records=None):
    """Punto de entrada principal."""
    categorizer = REPDCategorizerLLM()
    return categorizer.run(max_records)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--max', type=int, default=None,
                       help='Máximo de registros a procesar')
    args = parser.parse_args()
    main(args.max)

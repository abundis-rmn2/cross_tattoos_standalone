"""
Cross Tattoos Standalone - DeepSeek Client

Client for DeepSeek API for LLM-based tattoo categorization.
Forked from: ds/shared.py
"""

import os
import json
import re
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import Config

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None
    print("Warning: openai package not installed. LLM features will be unavailable.")


class DeepSeekClient:
    """Client for interacting with DeepSeek API."""
    
    # Shared system prompt for tattoo categorization
    SYSTEM_PROMPT = {
        "role": "system",
        "content": (
            "Eres un médico forense experto en tatuajes. Tu tarea es analizar "
            "descripciones de tatuajes y categorizarlos de manera consistente. "
            "Responde solo con un arreglo en formato Python, sin explicaciones adicionales."
        )
    }
    
    def __init__(self, api_key=None):
        """
        Initialize DeepSeek client.
        
        Args:
            api_key: Optional API key. If None, uses Config.DEEPSEEK_API_KEY
        """
        self.api_key = api_key or Config.DEEPSEEK_API_KEY
        self.model = Config.DEEPSEEK_MODEL
        self.max_tokens = Config.LLM_MAX_TOKENS
        self.temperature = Config.LLM_TEMPERATURE
        
        if not self.api_key:
            print("Warning: DEEPSEEK_API_KEY not configured. Set it in .env file.")
        
        if OpenAI is None:
            print("Warning: openai package not installed. Run: pip install openai")
            self.client = None
        elif self.api_key:
            self.client = OpenAI(
                api_key=self.api_key, 
                base_url="https://api.deepseek.com"
            )
        else:
            self.client = None
    
    def generate(self, prompt, system_prompt=None):
        """
        Send a prompt to the DeepSeek API and return the generated response.
        
        Args:
            prompt: User prompt to send
            system_prompt: Optional custom system prompt
            
        Returns:
            Generated response string or None on error
        """
        if self.client is None:
            print("Error: DeepSeek client not initialized")
            return None
        
        system = system_prompt or self.SYSTEM_PROMPT
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    system,
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=False
            )
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error calling DeepSeek API: {e}")
            return None
    
    def clean_response(self, response):
        """
        Clean the response to extract only the JSON array.
        
        Args:
            response: Raw response from API
            
        Returns:
            Cleaned JSON string
            
        Raises:
            ValueError: If response is not a valid JSON array
        """
        if response is None:
            raise ValueError("Response is None")
        
        # Remove markdown code blocks (```json or ```python)
        response = re.sub(r"```json|```python|```", "", response).strip()
        
        # Ensure the response is a valid JSON array
        if not response.startswith("[") or not response.endswith("]"):
            raise ValueError("Response is not a valid JSON array")
        
        return response
    
    def parse_tattoo_response(self, response):
        """
        Parse tattoo categorization response.
        
        Args:
            response: Raw API response
            
        Returns:
            List of dictionaries with tattoo data
            
        Raises:
            ValueError: If parsing fails
        """
        cleaned = self.clean_response(response)
        return json.loads(cleaned)
    
    def categorize_tattoo(self, id_persona, tattoo_description):
        """
        Categorize a single tattoo description.
        
        Args:
            id_persona: Person ID
            tattoo_description: Tattoo description text
            
        Returns:
            List of dictionaries with categorized tattoos
        """
        prompt = f"""
        Eres un médico forense experto en tatuajes. Tu tarea es categorizar los siguientes tatuajes en un arreglo de Python. Para cada tatuaje, crea un registro y proporciona una descripción clara y concisa que incluya su ubicación, texto extraído, categorías y palabras clave.

        Instrucciones:
        1. Asegúrate de que cada tatuaje se describa solo una vez. No repitas tatuajes.
        2. Devuelve un arreglo JSON válido y completo.
        3. Si hay múltiples tatuajes, crea un registro separado para cada uno.

        Tatuajes:
        {tattoo_description}

        Formato de salida:
        [
            {{
                "id_persona": "{id_persona}",
                "descripcion_original": "{tattoo_description}",
                "descripcion_tattoo": "Descripción del tatuaje individual",
                "ubicacion": "Ubicación del tatuaje",
                "texto_extraido": "Texto extraído del tatuaje individual",
                "categorias": "Categorías del tatuaje individual",
                "palabras_clave": "Palabras clave del tatuaje individual, separadas por coma",
                "diseño": "Diseño específico del tatuaje individual"
            }}
        ]
        """
        
        response = self.generate(prompt)
        
        if response:
            try:
                return self.parse_tattoo_response(response)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Failed to parse response: {e}")
                return None
        
        return None


def generate_with_deepseek_api(prompt, api_key):
    """
    Legacy function for compatibility.
    
    Args:
        prompt: Prompt to send
        api_key: DeepSeek API key
        
    Returns:
        Generated response
    """
    client = DeepSeekClient(api_key)
    return client.generate(prompt)


def clean_response(response):
    """Legacy function for compatibility."""
    client = DeepSeekClient()
    return client.clean_response(response)

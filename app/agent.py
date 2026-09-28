import os
import json
import logging
from google import genai
from google.genai import types

logger = logging.getLogger('TutorGebraAgent')

def generate_geogebra_script(prompt: str) -> dict:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("No se encontro la variable de entorno GEMINI_API_KEY. Configurala en la UI o en tu sistema.")
        
    client = genai.Client(api_key=api_key)
    
    prompt_path = os.path.join(os.path.dirname(__file__), "system_prompt.md")
    with open(prompt_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()
    
    logger.info(f"Enviando prompt a Gemini: {prompt}")
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            temperature=0.7
        )
    )
    
    try:
        data = json.loads(response.text)
        return data
    except Exception as e:
        logger.error(f"Error parseando respuesta JSON: {e}")
        logger.error(f"Respuesta cruda: {response.text}")
        raise

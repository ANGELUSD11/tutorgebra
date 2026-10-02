import os
import json
import logging
import base64
from google import genai
from google.genai import types, errors

logger = logging.getLogger('TutorGebraAgent')

def generate_geogebra_script(prompt: str, api_key: str, image_b64: str = None) -> dict:
    if not api_key:
        raise ValueError("API Key is missing.")
        
    client = genai.Client(api_key=api_key)
    
    prompt_path = os.path.join(os.path.dirname(__file__), "system_prompt.md")
    with open(prompt_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()
    
    logger.info(f"Sending prompt to Gemini: {prompt}")
    
    contents = [prompt]
    if image_b64:
        image_bytes = base64.b64decode(image_b64)
        # Using image/jpeg as a fallback, gemini usually handles png/jpg fine
        image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
        contents.append(image_part)
        logger.info("Included image in the prompt")
    
    try:
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=0.7
            )
        )
    except errors.APIError as e:
        logger.error(f"Gemini API Error: {e}")
        if e.code == 503:
            raise Exception("Google Gemini servers are currently experiencing high demand. Please try again in a few seconds.")
        elif e.code == 429:
            raise Exception("You have reached the API request limit or your quota is exhausted. Please try again later.")
        else:
            raise Exception(f"AI Connection Error ({e.code}): {e.message}")
    
    try:
        data = json.loads(response.text)
        return data
    except Exception as e:
        logger.error(f"Error parsing JSON response: {e}")
        logger.error(f"Raw response: {response.text}")
        raise

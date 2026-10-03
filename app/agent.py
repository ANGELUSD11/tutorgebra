import os
import json
import logging
import base64
from openrouter import OpenRouter

logger = logging.getLogger('TutorGebraAgent')

def generate_geogebra_script(prompt: str, api_key: str = "", image_b64: str = None) -> dict:
    final_api_key = api_key.strip() if api_key else os.environ.get("OPENROUTER_API_KEY")
    if not final_api_key:
        raise ValueError("OpenRouter API Key is missing. Please provide one in the UI or configure the server with OPENROUTER_API_KEY.")
        
    client = OpenRouter(api_key=final_api_key)
    
    prompt_path = os.path.join(os.path.dirname(__file__), "system_prompt.md")
    with open(prompt_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()
    
    logger.info(f"Sending prompt to OpenRouter: {prompt}")
    
    user_content = [{"type": "text", "text": prompt}]
    if image_b64:
        user_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{image_b64}"
            }
        })
        logger.info("Included image in the prompt")
        
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]
    
    try:
        response = client.chat.send(
            # OpenRouter Fallback system limits the array to 3 items max.
            models=[
                'google/gemini-3.8-flash',
                'openai/gpt-4o-mini',
                'anthropic/claude-3.5-haiku'
            ],
            messages=messages,
            response_format={'type': 'json_object'},
            temperature=0.7,
            max_tokens=1500
        )
        logger.info(f"OpenRouter successfully routed the request to model: {response.model}")
    except Exception as e:
        logger.error(f"OpenRouter API Error: {e}")
        raise Exception(f"AI Connection Error: {e}")
    
    try:
        content = response.choices[0].message.content
        
        clean_content = content.strip()
        if clean_content.startswith("```json"):
            clean_content = clean_content[7:]
        elif clean_content.startswith("```"):
            clean_content = clean_content[3:]
            
        if clean_content.endswith("```"):
            clean_content = clean_content[:-3]
            
        clean_content = clean_content.strip()
        
        data = json.loads(clean_content)
        return data
    except json.JSONDecodeError as e:
        logger.error(f"JSON Parsing Error: {e}")
        logger.error(f"Raw response: {content if 'content' in locals() else 'None'}")
        raise Exception("The response was cut off or the math problem was too broad/long. Please try asking for a shorter exercise, or break it down into smaller parts.")
    except Exception as e:
        logger.error(f"General Error parsing response: {e}")
        raise Exception(f"AI Processing Error: {e}")

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
        
    target_models = [
        'openai/gpt-4o',
        'anthropic/claude-sonnet-5.5',
        'openai/gpt-4o-mini'
    ]

    if image_b64:
        try:
            logger.info("Performing preliminary OCR and Difficulty Classification with gpt-4o-mini...")
            ocr_messages = [
                {
                    "role": "system",
                    "content": "You are a Math OCR and Classifier. Read the image and prompt. 1. Extract all text/math perfectly. 2. Classify difficulty. If it's university-level (physics, advanced calculus, abstract algebra, PDEs, etc.), output 'advanced'. If high-school level or simple drawings, output 'basic'. Return EXACTLY JSON: {\"extracted_text\": \"...\", \"difficulty\": \"basic\" | \"advanced\"}"
                },
                {"role": "user", "content": user_content}
            ]
            
            # Use cheap Vision model for OCR
            ocr_resp = client.chat.send(
                models=['openai/gpt-4o-mini'],
                messages=ocr_messages,
                response_format={'type': 'json_object'},
                temperature=0.1,
                max_tokens=1000
            )
            
            ocr_content = ocr_resp.choices[0].message.content
            clean_ocr = ocr_content.strip()
            if clean_ocr.startswith("```json"): clean_ocr = clean_ocr[7:]
            elif clean_ocr.startswith("```"): clean_ocr = clean_ocr[3:]
            if clean_ocr.endswith("```"): clean_ocr = clean_ocr[:-3]
            clean_ocr = clean_ocr.strip()
            
            ocr_data = json.loads(clean_ocr)
            difficulty = ocr_data.get("difficulty", "basic").lower()
            extracted = ocr_data.get("extracted_text", "")
            
            logger.info(f"Problem classified as: {difficulty}")
            
            if difficulty == "advanced":
                logger.info("Advanced problem detected! Routing text to Claude Sonnet 5.5 and stripping image to save Vision costs.")
                # Replace the image with the extracted text!
                user_content = [
                    {"type": "text", "text": f"User Request: {prompt}\n\n[Extracted Mathematical Content from User's Image]:\n{extracted}\n\n(CRITICAL: Solve this advanced problem step-by-step, but you MUST provide all 'speech' explanations in the EXACT SAME LANGUAGE as the User Request above)."}
                ]
                target_models = ['anthropic/claude-sonnet-5.5', 'openai/gpt-4o']
            else:
                logger.info("Basic problem detected. Proceeding normally.")
                
        except Exception as e:
            logger.warning(f"Smart Routing failed, falling back to standard pipeline: {e}")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]
    
    max_retries = 2
    for attempt in range(max_retries):
        try:
            logger.info(f"Generation attempt {attempt + 1} with target models: {target_models}")
            response = client.chat.send(
                models=target_models,
                messages=messages,
                temperature=0.7,
                max_tokens=1200
            )
            logger.info(f"OpenRouter successfully routed the request to model: {response.model}")
            
            content = response.choices[0].message.content
            
            clean_content = content.strip()
            if clean_content.startswith("```json"): clean_content = clean_content[7:]
            elif clean_content.startswith("```"): clean_content = clean_content[3:]
            if clean_content.endswith("```"): clean_content = clean_content[:-3]
            clean_content = clean_content.strip()
            
            data = json.loads(clean_content)
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON Parsing Error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                logger.info("JSON was truncated or malformed. Forcing fallback to gpt-4o-mini for the next attempt...")
                target_models = ['openai/gpt-4o-mini']
                continue
            logger.error(f"Raw response: {content if 'content' in locals() else 'None'}")
            raise Exception("The response was repeatedly cut off. Please try asking for a shorter exercise, or check your API credits.")
            
        except Exception as e:
            logger.error(f"General Error: {e}")
            if attempt < max_retries - 1:
                target_models = ['openai/gpt-4o-mini']
                continue
            raise Exception(f"AI Processing Error: {e}")

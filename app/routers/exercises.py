import asyncio
import json
import logging
import traceback
import uuid
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse

from app.security import (
    get_client_ip,
    check_rate_limit_memory,
    read_json_body,
    get_str_field,
    ALLOWED_GTTS_VOICES,
    ALLOWED_MODELS,
    MAX_BODY_BYTES,
    MAX_IMAGE_B64_CHARS,
    MAX_PROMPT_CHARS,
    MAX_API_KEY_CHARS,
    MAX_SHORT_FIELD_CHARS,
)
from app.redis_rate_limit import check_rate_limit_redis
from app.agent import generate_geogebra_script, sanitize_geogebra_command
from app.bot import (
    _generate_single_edge_audio,
    _generate_single_audio,
    global_tts_semaphore,
)

logger = logging.getLogger('TutorGebraExercises')

router = APIRouter(prefix="/api", tags=["exercises"])

@router.post("/run")
async def run_exercise(req: Request):
    # Get real user IP from the trusted proxy hop (see get_client_ip)
    client_ip = get_client_ip(req)

    # Bot Protection: Check for custom header to block simple curl/script bots
    client_header = req.headers.get("x-tutor-client")
    if client_header != "TutorGebraWeb":
        logger.warning(f"Bot blocked. Missing or invalid client header from IP: {client_ip}")
        raise HTTPException(status_code=403, detail="Forbidden. Please use the official web interface.")

    # Try to use Redis Global Rate Limiting first
    redis_handled = await check_rate_limit_redis(client_ip, limit=5, window=60)
    
    # If Redis is disconnected or fails, fallback to local memory limit
    if not redis_handled:
        check_rate_limit_memory(client_ip)

    body = await read_json_body(req, MAX_BODY_BYTES)
    prompt = get_str_field(body, "prompt", MAX_PROMPT_CHARS, default="")
    api_key = get_str_field(body, "api_key", MAX_API_KEY_CHARS, default="")
    voice = get_str_field(body, "voice", MAX_SHORT_FIELD_CHARS, default="auto")
    edge_voice = get_str_field(body, "edge_voice", MAX_SHORT_FIELD_CHARS)
    image_b64 = get_str_field(body, "image", MAX_IMAGE_B64_CHARS)
    selected_model = get_str_field(body, "selected_model", MAX_SHORT_FIELD_CHARS) or "auto"

    if not prompt.strip() and not image_b64:
        raise HTTPException(status_code=400, detail="Debes ingresar un ejercicio o adjuntar una imagen.")

    # Fix #2: only allow known models (prevents arbitrary/expensive models on the server key)
    if not isinstance(selected_model, str) or selected_model not in ALLOWED_MODELS:
        logger.warning(f"Rejected unsupported model from IP {client_ip}: {selected_model!r:.100}")
        raise HTTPException(status_code=400, detail="Modelo no soportado.")

    # Fix #1: resolve gTTS (lang, tld) strictly from the allowlist (prevents SSRF via tld)
    gtts_override = None
    if voice and voice != "auto":
        if not isinstance(voice, str) or voice not in ALLOWED_GTTS_VOICES:
            logger.warning(f"Rejected unsupported voice from IP {client_ip}: {voice!r:.100}")
            raise HTTPException(status_code=400, detail="Voz no soportada.")
        gtts_override = ALLOWED_GTTS_VOICES[voice]
        
    async def event_stream():
        try:
            yield f"data: {json.dumps({'status': 'progress', 'message': 'Thinking about the mathematical solution...', 'percent': 10})}\n\n"
            
            session_id = str(uuid.uuid4())
            # Run Gemini in thread to prevent blocking loop
            data = await asyncio.to_thread(generate_geogebra_script, prompt, api_key, image_b64, selected_model)
            raw_steps = data.get("steps", [])
            if isinstance(raw_steps, dict):
                raw_steps = [raw_steps]
            elif not isinstance(raw_steps, list):
                raw_steps = []
                
            steps = []
            for s in raw_steps:
                if isinstance(s, dict):
                    cmd = sanitize_geogebra_command(s.get("command", ""))
                    steps.append({"command": cmd, "speech": s.get("speech", "")})
                elif isinstance(s, str):
                    steps.append({"command": "", "speech": s})
                    
            lang = data.get("language", "en")
            tld = "com"
            
            # lang/tld come only from the server-side allowlist, never from raw user text
            if gtts_override:
                lang, tld = gtts_override
                    
            yield f"data: {json.dumps({'status': 'progress', 'message': f'Lesson generated ({len(steps)} steps). Synthesizing teacher voice...', 'percent': 30})}\n\n"
            
            tasks = []
            if edge_voice:
                for i, step in enumerate(steps):
                    tasks.append(_generate_single_edge_audio(step, edge_voice, session_id, i))
            else:
                async def bounded_gtts_audio(s, lang, tld, sid, idx):
                    async with global_tts_semaphore:
                        return await asyncio.to_thread(_generate_single_audio, s, lang, tld, sid, idx)
                        
                for i, step in enumerate(steps):
                    tasks.append(bounded_gtts_audio(step, lang, tld, session_id, i))
            
            completed = 0
            total = len(tasks)
            
            for coro in asyncio.as_completed(tasks):
                if await req.is_disconnected():
                    logger.info("Client disconnected. Aborting audio synthesis.")
                    break
                    
                await coro
                completed += 1
                percent = 30 + int((completed / total) * 70)
                
                # Check disconnect again before yielding
                if await req.is_disconnected():
                    break
                    
                yield f"data: {json.dumps({'status': 'progress', 'message': f'Synthesizing audio step {completed}/{total}...', 'percent': percent})}\n\n"
            
            if not await req.is_disconnected():
                yield f"data: {json.dumps({'status': 'done', 'steps': steps, 'session_id': session_id, 'meta': data.get('_meta', {})})}\n\n"
        except Exception as e:
            logger.error("Critical error in bot execution:")
            logger.error(traceback.format_exc())
            if not await req.is_disconnected():
                yield f"data: {json.dumps({'status': 'error', 'detail': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


import asyncio
import logging
import traceback
import uvicorn
import time
import shutil
import uuid
import json
import os
import ipaddress

from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

from app.agent import generate_geogebra_script
from app.bot import pregenerate_audio

# Load environment variables from .env file for local development
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('TutorGebraWeb')

from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from app.redis_rate_limit import init_redis, close_redis, check_rate_limit_redis

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Dynamically expand thread pool for blocking I/O (Gemini API & gTTS) up to 200 workers during traffic spikes
    loop = asyncio.get_running_loop()
    loop.set_default_executor(ThreadPoolExecutor(max_workers=200))
    
    await init_redis()
    
    # Clean up immediately on startup
    await asyncio.to_thread(cleanup_old_audios)
    # Start periodic background cleanup task
    task = asyncio.create_task(periodic_cleanup())
    yield
    # Clean up background task on shutdown
    task.cancel()
    await close_redis()

# Detect if we are running in a production environment (like Railway)
is_production = os.environ.get("ENVIRONMENT", "").lower() == "production" or "RAILWAY_ENVIRONMENT_NAME" in os.environ

app = FastAPI(
    title="TutorGebra", 
    lifespan=lifespan,
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json"
)

# Configure allowed domains for CORS (Browsers)
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:8080",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8080",
    "https://tutorgebra-production.up.railway.app",
]

env_origins = os.environ.get("ALLOWED_ORIGINS")
if env_origins:
    origins.extend([o.strip() for o in env_origins.split(",")])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "DELETE"],
    allow_headers=["*"],
)

static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
os.makedirs(static_path, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_path), name="static")

audios_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "audios")
os.makedirs(audios_path, exist_ok=True)
app.mount("/audios", StaticFiles(directory=audios_path), name="audios")

class ExerciseRequest(BaseModel):
    prompt: str
    api_key: str
    voice: str = "auto"

from fastapi.responses import FileResponse, StreamingResponse
@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    index_path = os.path.join(static_path, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/favicon.ico")
async def favicon():
    return FileResponse(os.path.join(static_path, "favicon.ico"))

def cleanup_old_audios():
    try:
        if not os.path.exists(audios_path):
            return
        now = time.time()
        for foldername in os.listdir(audios_path):
            folder_path = os.path.join(audios_path, foldername)
            if os.path.isdir(folder_path):
                # Delete folders older than 30 minutes
                if os.stat(folder_path).st_mtime < now - 1800:
                    shutil.rmtree(folder_path, ignore_errors=True)
    except Exception as e:
        logger.error(f"Error cleaning up old audios: {e}")

async def periodic_cleanup():
    while True:
        await asyncio.to_thread(cleanup_old_audios)
        sweep_rate_limit_memory()  # Free memory from IPs that stopped sending requests
        await asyncio.sleep(600) # Run every 10 minutes

@app.api_route("/api/cleanup/{session_id}", methods=["POST", "DELETE"])
async def cleanup_session(session_id: str):
    # 1. Strict validation: session IDs are always uuid4, so reject anything else.
    #    A valid UUID cannot contain '/', '\\' or '..', which rules out path traversal.
    try:
        safe_session_id = str(uuid.UUID(session_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de session_id inválido.")

    try:
        base_dir = os.path.realpath(audios_path)
        folder_path = os.path.realpath(os.path.join(base_dir, safe_session_id))

        # 2. Defense in depth: the resolved path must be a direct child of the audios dir
        #    (also guards against symlinks pointing outside of it).
        if os.path.dirname(folder_path) != base_dir:
            raise HTTPException(status_code=400, detail="Formato de session_id inválido.")

        if os.path.isdir(folder_path):
            shutil.rmtree(folder_path, ignore_errors=True)
        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as e:
        # Log the real error, return a generic message to the client
        logger.error(f"Error in cleanup_session: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": "Error interno al procesar la solicitud."},
        )

# --- Client IP resolution (Fix #3) ---
# X-Forwarded-For is a comma-separated list where each proxy APPENDS the address it saw.
# The leftmost entries are written by the client and can be forged, so we only trust the
# entry added by our own proxy: the Nth from the right, where N = number of trusted proxies.
# If the proxy overwrites the header instead, there is a single entry and the result is the same.
TRUST_PROXY_HEADERS = os.environ.get("TRUST_PROXY_HEADERS", "1" if is_production else "0") == "1"
TRUSTED_PROXY_HOPS = max(1, int(os.environ.get("TRUSTED_PROXY_HOPS", "1")))

def get_client_ip(req: Request) -> str:
    peer_ip = req.client.host if req.client else "unknown"
    if not TRUST_PROXY_HEADERS:
        # Local/dev: there is no proxy in front, so any X-Forwarded-For would be client-forged
        return peer_ip

    xff = req.headers.get("x-forwarded-for", "")
    hops = [h.strip() for h in xff.split(",") if h.strip()]
    if not hops:
        return peer_ip

    candidate = hops[-TRUSTED_PROXY_HOPS] if len(hops) >= TRUSTED_PROXY_HOPS else hops[0]
    try:
        # Normalizes the value and rejects garbage, so it can't be used to create arbitrary keys
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        logger.warning(f"Invalid X-Forwarded-For value {candidate!r:.60}; using peer IP")
        return peer_ip

# Simple In-Memory Rate Limiter (Fallback Anti-DDoS Layer 7)
RATE_LIMIT = 5  # Max requests
RATE_LIMIT_WINDOW = 60  # Per 60 seconds
MAX_TRACKED_IPS = 10_000  # Force a sweep above this many entries to bound memory usage
ip_requests = defaultdict(list)

def sweep_rate_limit_memory():
    """Drop IPs with no requests inside the current window so the dict can't grow forever."""
    cutoff = time.time() - RATE_LIMIT_WINDOW
    stale = [ip for ip, timestamps in ip_requests.items() if not timestamps or timestamps[-1] < cutoff]
    for ip in stale:
        ip_requests.pop(ip, None)

def check_rate_limit_memory(client_ip: str):
    now = time.time()

    if len(ip_requests) > MAX_TRACKED_IPS:
        sweep_rate_limit_memory()
    
    # Clean up requests older than the window
    ip_requests[client_ip] = [t for t in ip_requests[client_ip] if now - t < RATE_LIMIT_WINDOW]
    
    if len(ip_requests[client_ip]) >= RATE_LIMIT:
        logger.warning(f"Local memory rate limit exceeded for IP: {client_ip}")
        raise HTTPException(status_code=429, detail="Too many requests. Please wait a minute before generating another lesson.")
        
    ip_requests[client_ip].append(now)

# Allowlists (must mirror the options offered in static/app.js).
# gTTS voices map to a fixed (lang, tld) pair: the tld is interpolated by gTTS into
# "https://translate.google.{tld}/...", so it must never come from user input (SSRF).
ALLOWED_GTTS_VOICES = {
    "es-es": ("es", "es"),
    "es-com.mx": ("es", "com.mx"),
    "en-us": ("en", "us"),
    "en-co.uk": ("en", "co.uk"),
}

# Models billed to the server's OPENROUTER_API_KEY; anything else is rejected (cost abuse).
ALLOWED_MODELS = {
    "auto",
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    "anthropic/claude-sonnet-5.5",
}

# --- Input size limits (Fix #4) ---
MAX_BODY_BYTES = 6 * 1024 * 1024   # 6 MB for the whole JSON body
MAX_IMAGE_B64_CHARS = 5_000_000    # ~3.7 MB decoded image (the frontend downscales before sending)
MAX_PROMPT_CHARS = 550
MAX_API_KEY_CHARS = 256
MAX_SHORT_FIELD_CHARS = 64         # voice, edge_voice, selected_model

async def read_json_body(req: Request, max_bytes: int) -> dict:
    """Read the request body with a hard size cap instead of loading it blindly into memory."""
    content_length = req.headers.get("content-length")
    if content_length is not None:
        try:
            if int(content_length) > max_bytes:
                raise HTTPException(status_code=413, detail="La solicitud es demasiado grande.")
        except ValueError:
            raise HTTPException(status_code=400, detail="Content-Length inválido.")

    # Also enforced while streaming, because chunked requests may omit Content-Length
    chunks, size = [], 0
    async for chunk in req.stream():
        size += len(chunk)
        if size > max_bytes:
            raise HTTPException(status_code=413, detail="La solicitud es demasiado grande.")
        chunks.append(chunk)

    try:
        body = json.loads(b"".join(chunks))
    except (ValueError, UnicodeDecodeError):
        raise HTTPException(status_code=400, detail="JSON inválido.")
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="JSON inválido.")
    return body

def get_str_field(body: dict, key: str, max_len: int, default=None):
    """Return an optional string field, rejecting wrong types and oversized values."""
    value = body.get(key)
    if value is None:
        return default
    if not isinstance(value, str):
        raise HTTPException(status_code=400, detail=f"Campo '{key}' inválido.")
    if len(value) > max_len:
        raise HTTPException(status_code=413, detail=f"El campo '{key}' es demasiado largo.")
    return value

@app.post("/api/run")
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
                    steps.append(s)
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
                from app.bot import _generate_single_edge_audio
                for i, step in enumerate(steps):
                    tasks.append(_generate_single_edge_audio(step, edge_voice, session_id, i))
            else:
                from app.bot import _generate_single_audio, global_tts_semaphore
                
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting TutorGebra UI at http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

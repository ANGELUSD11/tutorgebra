import os
import time
import json
import logging
import ipaddress
from collections import defaultdict
from fastapi import Request, HTTPException

from app.config import IS_PRODUCTION

logger = logging.getLogger('TutorGebraSecurity')

# --- Client IP resolution ---
# X-Forwarded-For is a comma-separated list where each proxy APPENDS the address it saw.
# The leftmost entries are written by the client and can be forged, so we only trust the
# entry added by our own proxy: the Nth from the right, where N = number of trusted proxies.
TRUST_PROXY_HEADERS = os.environ.get("TRUST_PROXY_HEADERS", "1" if IS_PRODUCTION else "0") == "1"
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

# --- In-Memory Rate Limiter (Fallback Anti-DDoS Layer 7) ---
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

# --- Allowlists ---
# gTTS voices map to a fixed (lang, tld) pair: the tld is interpolated by gTTS into
# "https://translate.google.{tld}/...", so it must never come from user input (SSRF).
ALLOWED_GTTS_VOICES = {
    "es-es": ("es", "es"),
    "es-com.mx": ("es", "com.mx"),
    "en-us": ("en", "us"),
    "en-co.uk": ("en", "co.uk"),
}

# Edge TTS voices offered by the UI. edge-tts interpolates the voice name into the SSML
# it sends to Microsoft without escaping it, so it must never come from raw user input.
ALLOWED_EDGE_VOICES = {
    "es-MX-JorgeNeural",
    "es-MX-DaliaNeural",
    "es-ES-AlvaroNeural",
    "es-ES-ElviraNeural",
    "en-US-GuyNeural",
    "en-US-JennyNeural",
}

# Models billed to the server's OPENROUTER_API_KEY; anything else is rejected (cost abuse).
ALLOWED_MODELS = {
    "auto",
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    "anthropic/claude-sonnet-5.5",
}

# --- Input size limits ---
MAX_BODY_BYTES = 6 * 1024 * 1024   # 6 MB for the whole JSON body
MAX_IMAGE_B64_CHARS = 5_000_000    # ~3.7 MB decoded image (the frontend downscales before sending)
MAX_PROMPT_CHARS = 1000
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


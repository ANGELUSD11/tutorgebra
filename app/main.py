import asyncio
import logging
import traceback
import os
from collections import defaultdict
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from app.agent import generate_geogebra_script
from app.bot import pregenerate_audio

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('TutorGebraWeb')

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Clean up immediately on startup
    await asyncio.to_thread(cleanup_old_audios)
    # Start periodic background cleanup task
    task = asyncio.create_task(periodic_cleanup())
    yield
    # Clean up background task on shutdown
    task.cancel()

app = FastAPI(title="TutorGebra", lifespan=lifespan)

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
    return FileResponse(os.path.join(static_path, "favicon.png"))

import time
import shutil
import uuid
import json

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
        await asyncio.sleep(600) # Run every 10 minutes

@app.api_route("/api/cleanup/{session_id}", methods=["POST", "DELETE"])
async def cleanup_session(session_id: str):
    try:
        # Sanitize session_id to prevent path traversal
        session_id = os.path.basename(session_id)
        folder_path = os.path.join(audios_path, session_id)
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            shutil.rmtree(folder_path, ignore_errors=True)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

# Simple In-Memory Rate Limiter (Anti-DDoS Layer 7)
RATE_LIMIT = 5  # Max requests
RATE_LIMIT_WINDOW = 60  # Per 60 seconds
ip_requests = defaultdict(list)

def check_rate_limit(request: Request):
    # Get IP, accounting for PaaS reverse proxies like Railway or Cloudflare
    client_ip = request.headers.get("x-forwarded-for", request.client.host).split(",")[0].strip()
    now = time.time()
    
    # Clean up requests older than the window
    ip_requests[client_ip] = [t for t in ip_requests[client_ip] if now - t < RATE_LIMIT_WINDOW]
    
    if len(ip_requests[client_ip]) >= RATE_LIMIT:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(status_code=429, detail="Too many requests. Please wait a minute before generating another lesson.")
        
    ip_requests[client_ip].append(now)

@app.post("/api/run")
async def run_exercise(req: Request):
    check_rate_limit(req)
    body = await req.json()
    prompt = body.get("prompt", "")
    api_key = body.get("api_key", "")
    voice = body.get("voice", "auto")
    edge_voice = body.get("edge_voice")
        
    async def event_stream():
        try:
            yield f"data: {json.dumps({'status': 'progress', 'message': 'Thinking about the mathematical solution...', 'percent': 10})}\n\n"
            
            session_id = str(uuid.uuid4())
            # Run Gemini in thread to prevent blocking loop
            data = await asyncio.to_thread(generate_geogebra_script, prompt, api_key)
            steps = data.get("steps", [])
            lang = data.get("language", "en")
            tld = "com"
            
            if voice and voice != "auto":
                parts = voice.split('-')
                if len(parts) == 2:
                    lang = parts[0]
                    tld = parts[1]
                    
            yield f"data: {json.dumps({'status': 'progress', 'message': f'Lesson generated ({len(steps)} steps). Synthesizing teacher voice...', 'percent': 30})}\n\n"
            
            tasks = []
            if edge_voice:
                from bot import _generate_single_edge_audio
                for i, step in enumerate(steps):
                    tasks.append(_generate_single_edge_audio(step, edge_voice, session_id))
            else:
                from bot import _generate_single_audio
                for i, step in enumerate(steps):
                    tasks.append(asyncio.to_thread(_generate_single_audio, step, lang, tld, session_id))
            
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
                yield f"data: {json.dumps({'status': 'done', 'steps': steps, 'session_id': session_id})}\n\n"
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

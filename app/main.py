import asyncio
import json
import logging
import os
import shutil
import time
import uvicorn
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from app.config import STATIC_PATH, AUDIOS_PATH, IS_PRODUCTION
from app.redis_rate_limit import init_redis, close_redis
from app.security import sweep_rate_limit_memory, MAX_PROMPT_CHARS
from app.routers import exercises, sessions

# Load environment variables from .env file for local development
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('TutorGebraWeb')

def cleanup_old_audios():
    try:
        if not os.path.exists(AUDIOS_PATH):
            return
        now = time.time()
        for foldername in os.listdir(AUDIOS_PATH):
            folder_path = os.path.join(AUDIOS_PATH, foldername)
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
        await asyncio.sleep(600)   # Run every 10 minutes

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

app = FastAPI(
    title="TutorGebra", 
    lifespan=lifespan,
    docs_url=None if IS_PRODUCTION else "/docs",
    redoc_url=None if IS_PRODUCTION else "/redoc",
    openapi_url=None if IS_PRODUCTION else "/openapi.json"
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

# Static file mounts
os.makedirs(STATIC_PATH, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_PATH), name="static")

os.makedirs(AUDIOS_PATH, exist_ok=True)
app.mount("/audios", StaticFiles(directory=AUDIOS_PATH), name="audios")

# Include Routers
app.include_router(exercises.router)
app.include_router(sessions.router)

# Main web routes kept in main.py
@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    index_path = os.path.join(STATIC_PATH, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()
    # Single source of truth for limits shared with the frontend (see app/security.py)
    client_config = json.dumps({"maxPromptChars": MAX_PROMPT_CHARS})
    content = content.replace("</head>", f"<script>window.TUTOR_CONFIG = {client_config};</script>\n</head>", 1)
    return HTMLResponse(
        content=content,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/favicon.ico")
async def favicon():
    return FileResponse(os.path.join(STATIC_PATH, "favicon.ico"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting TutorGebra UI at http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

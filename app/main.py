import asyncio
import logging
import traceback
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from agent import generate_geogebra_script
from bot import pregenerate_audio

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('TutorGebraWeb')

app = FastAPI(title="TutorGebra")

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

from fastapi.responses import FileResponse

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

def cleanup_old_audios():
    try:
        now = time.time()
        for foldername in os.listdir(audios_path):
            folder_path = os.path.join(audios_path, foldername)
            if os.path.isdir(folder_path):
                # Delete folders older than 30 minutes
                if os.stat(folder_path).st_mtime < now - 1800:
                    shutil.rmtree(folder_path, ignore_errors=True)
    except Exception as e:
        logger.error(f"Error cleaning up old audios: {e}")

@app.delete("/api/cleanup/{session_id}")
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

@app.post("/api/run")
async def run_exercise(req: ExerciseRequest):
    # Background cleanup of old audios so server disk doesn't fill up
    asyncio.create_task(asyncio.to_thread(cleanup_old_audios))
        
    try:
        session_id = str(uuid.uuid4())
        data = generate_geogebra_script(req.prompt, req.api_key)
        steps = data.get("steps", [])
        lang = data.get("language", "en")
        tld = "com"
        
        if req.voice != "auto":
            parts = req.voice.split('-')
            if len(parts) == 2:
                lang = parts[0]
                tld = parts[1]
                
        # Generate audios and attach their URLs
        steps_with_audio = await asyncio.to_thread(pregenerate_audio, steps, lang, tld, session_id)
        
        return {"steps": steps_with_audio, "session_id": session_id}
    except Exception as e:
        logger.error("Critical error in bot execution:")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting TutorGebra UI at http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

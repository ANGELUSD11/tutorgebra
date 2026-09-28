import asyncio
import logging
import traceback
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import os

from agent import generate_geogebra_script
from bot import run_geogebra_session

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

class ExerciseRequest(BaseModel):
    prompt: str
    api_key: str

bot_status = {"state": "idle", "message": ""}

@app.post("/api/run")
async def run_exercise(req: ExerciseRequest):
    global bot_status
    if req.api_key:
        os.environ["GEMINI_API_KEY"] = req.api_key
        
    try:
        bot_status = {"state": "generating", "message": "Generating lesson plan..."}
        data = generate_geogebra_script(req.prompt)
        
        bot_status = {"state": "running", "message": "Teaching lesson in GeoGebra..."}
        asyncio.create_task(run_bot_safe(data))
        
        return {"status": "success", "steps": data.get("steps", [])}
    except Exception as e:
        bot_status = {"state": "error", "message": str(e)}
        logger.error(f"Error procesando solicitud: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def run_bot_safe(data):
    global bot_status
    try:
        await run_geogebra_session(data)
        bot_status = {"state": "finished", "message": "Lesson successfully finished!"}
    except Exception as e:
        error_msg = str(e)
        if "TargetClosedError" in error_msg or "Target page, context or browser has been closed" in error_msg:
            logger.warning("El usuario cerro la ventana del navegador prematuramente.")
            bot_status = {"state": "error", "message": "Browser window was closed manually before the lesson finished."}
        else:
            logger.error("Error critico en la ejecucion del bot:")
            logger.error(traceback.format_exc())
            bot_status = {"state": "error", "message": "Unexpected error during the lesson."}

@app.get("/api/status")
async def get_status():
    return bot_status

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "index.html"), "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    logger.info("Iniciando TutorGebra UI en http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)



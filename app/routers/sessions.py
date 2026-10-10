import os
import uuid
import shutil
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.config import AUDIOS_PATH

logger = logging.getLogger('TutorGebraSessions')

router = APIRouter(prefix="/api/cleanup", tags=["cleanup"])

@router.api_route("/{session_id}", methods=["POST", "DELETE"])
async def cleanup_session(session_id: str):
    # 1. Strict validation: session IDs are always uuid4, so reject anything else.
    #    A valid UUID cannot contain '/', '\\' or '..', which rules out path traversal.
    try:
        safe_session_id = str(uuid.UUID(session_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de session_id inválido.")

    try:
        base_dir = os.path.realpath(AUDIOS_PATH)
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


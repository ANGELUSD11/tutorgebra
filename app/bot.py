import logging
import os
import concurrent.futures
from gtts import gTTS

logger = logging.getLogger('TutorGebraBot')

def _generate_single_audio(step, lang, tld, session_id):
    cmd = step.get("command", "")
    text = step.get("speech", "")
    if not text:
        return step
        
    safe_name = "".join(c if c.isalnum() else "_" for c in cmd)[:50]
    filename = f"{safe_name}.mp3"
    
    session_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "audios", session_id)
    os.makedirs(session_dir, exist_ok=True)
    
    filepath = os.path.join(session_dir, filename)
    
    if not os.path.exists(filepath):
        try:
            tts = gTTS(text=text, lang=lang, tld=tld)
            tts.save(filepath)
        except Exception as e:
            logger.error(f"Error generating audio for '{cmd}': {e}")
            
    if os.path.exists(filepath):
        import base64
        with open(filepath, "rb") as f:
            b64_data = base64.b64encode(f.read()).decode("utf-8")
        step["audio_url"] = f"data:audio/mp3;base64,{b64_data}"
        os.remove(filepath)
        
    return step

async def _generate_single_edge_audio(step, voice, session_id):
    import edge_tts
    cmd = step.get("command", "")
    text = step.get("speech", "")
    if not text:
        return step
        
    safe_name = "".join(c if c.isalnum() else "_" for c in cmd)[:50]
    filename = f"{safe_name}.mp3"
    
    session_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "audios", session_id)
    os.makedirs(session_dir, exist_ok=True)
    
    filepath = os.path.join(session_dir, filename)
    
    if not os.path.exists(filepath):
        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(filepath)
        except Exception as e:
            logger.error(f"Error generating Edge TTS for '{cmd}': {e}")
            
    if os.path.exists(filepath):
        import base64
        with open(filepath, "rb") as f:
            b64_data = base64.b64encode(f.read()).decode("utf-8")
        step["audio_url"] = f"data:audio/mp3;base64,{b64_data}"
        os.remove(filepath)
        
    return step

def pregenerate_audio(steps, lang="en", tld="com", session_id="default"):
    logger.info(f"Synthesizing teacher voice with gTTS in parallel ({lang}-{tld})...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(10, max(1, len(steps)))) as executor:
        futures = [executor.submit(_generate_single_audio, step, lang, tld, session_id) for step in steps]
        updated_steps = [f.result() for f in futures]
        
    logger.info("Audios ready.")
    return updated_steps
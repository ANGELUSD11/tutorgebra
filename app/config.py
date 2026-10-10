import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_PATH = os.path.join(BASE_DIR, "static")
AUDIOS_PATH = os.path.join(BASE_DIR, "audios")

# Detect if we are running in a production environment (like Railway)
IS_PRODUCTION = os.environ.get("ENVIRONMENT", "").lower() == "production" or "RAILWAY_ENVIRONMENT_NAME" in os.environ


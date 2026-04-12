import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
DB_PATH = os.getenv("DB_PATH", "workout.db")

# Ensure ADK uses AI Studio, not Vertex AI
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "FALSE")

if not GOOGLE_API_KEY:
    raise RuntimeError(
        "GOOGLE_API_KEY is not set. Copy .env.example to .env and add your key."
    )

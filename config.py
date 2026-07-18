"""
Configuration for the multi-domain LLM voice agent.

No telephony provider is used anymore - the agent runs entirely in the
browser (mic in, speaker out) via the Web Speech API, so there's no
Twilio account, no verified caller IDs, and no per-minute calling cost.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

    # Public URL, only relevant if you deploy this so others can open the
    # dashboard/agent page remotely. Not required for local use.
    BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")

    # Groq LLM (free tier) - https://console.groq.com
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # Admin dashboard login (also used to access the /agent widget page)
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

    # Database
    DATABASE_FILE = os.getenv("DATABASE_FILE", "database.db")

    # Server port (Render/Railway set PORT automatically)
    PORT = int(os.getenv("PORT", "5000"))


def validate_config():
    warnings = []
    if not Config.GROQ_API_KEY:
        warnings.append("GROQ_API_KEY is not set - LLM responses will use basic fallback text only")
    if Config.ADMIN_PASSWORD == "admin123":
        warnings.append("Using default admin password - change ADMIN_PASSWORD before deploying publicly")
    return warnings

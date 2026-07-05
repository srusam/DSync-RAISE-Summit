import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

import os
from dotenv import load_dotenv

load_dotenv()

class Config:

    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-later")

    SQLALCHEMY_DATABASE_URI = \
        "sqlite:///" + os.path.join(BASE_DIR, "instance", "database.db")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    GRADIUM_API_KEY = os.getenv("GRADIUM_API_KEY")
    FIGMA_API_KEY = os.getenv("FIGMA_API_KEY")

    # Otari AI (OpenAI-compatible) — used for design review, handoff, PR compare
    OTARI_API_KEY = os.getenv("OTARI_API_KEY")
    OTARI_BASE_URL = os.getenv("OTARI_BASE_URL", "https://api.otari.ai/v1")
    OTARI_MODEL = os.getenv(
        "OTARI_MODEL",
        "mzai:moonshotai/Kimi-K2.6"
    )

    # GitHub — Phase 4 (add keys now so you don't touch config again later)
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")

UPLOAD_FOLDER = "uploads"
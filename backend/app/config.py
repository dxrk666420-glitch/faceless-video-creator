import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./faceless.db"

    # Optional API keys
    ELEVENLABS_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    PEXELS_API_KEY: str = ""
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    REDDIT_USER_AGENT: str = "FacelessVideoCreator/1.0"

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    MEDIA_DIR: Path = Path(__file__).resolve().parent.parent.parent / "media"
    UPLOADS_DIR: Path = Path(__file__).resolve().parent.parent.parent / "uploads"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

# Ensure directories exist
settings.MEDIA_DIR.mkdir(parents=True, exist_ok=True)
settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

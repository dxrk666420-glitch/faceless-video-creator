import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./faceless.db"

    # Supabase (set SUPABASE_DB_URL to use PostgreSQL instead of SQLite)
    SUPABASE_URL: str = ""        # e.g. https://xxxx.supabase.co
    SUPABASE_KEY: str = ""        # anon or service_role key
    SUPABASE_DB_URL: str = ""     # postgresql://postgres:...@db.xxxx.supabase.co:5432/postgres

    # Optional API keys
    ELEVENLABS_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""  # For AI story generation
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

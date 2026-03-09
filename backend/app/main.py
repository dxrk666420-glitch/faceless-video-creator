"""Faceless Video Creator - FastAPI Backend."""

import os
import re

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.routers import clipper, projects, reddit, sora, ugc
from app.schemas import JobStatus
from app.tasks.task_manager import task_manager

app = FastAPI(
    title="Faceless Video Creator",
    description="Create viral faceless videos - Reddit stories, AI-generated, auto-clipped, and UGC content",
    version="1.0.0",
)

# CORS - allow frontend (dev + production)
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
# Add production origin from env if set
if os.environ.get("FRONTEND_URL"):
    allowed_origins.append(os.environ["FRONTEND_URL"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(projects.router)
app.include_router(reddit.router)
app.include_router(sora.router)
app.include_router(clipper.router)
app.include_router(ugc.router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def root():
    return {
        "name": "Faceless Video Creator API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/api/jobs/{task_id}", response_model=JobStatus)
def get_job_status(task_id: str):
    """Check the status of an async video generation job."""
    # Validate task_id format to prevent injection
    if not re.match(r'^[a-zA-Z0-9_-]+$', task_id):
        return JobStatus(task_id=task_id, status="not_found", message="Invalid task ID")

    task = task_manager.get_task(task_id)
    if not task:
        return JobStatus(task_id=task_id, status="not_found", message="Task not found")
    return JobStatus(
        task_id=task.task_id,
        status=task.status,
        progress=task.progress,
        message=task.message,
        result=task.result,
    )


@app.get("/api/media/{filename}")
def serve_media(filename: str):
    """Serve generated video files."""
    # Security: prevent path traversal
    safe_name = os.path.basename(filename)
    if safe_name != filename or ".." in filename or "/" in filename:
        return JSONResponse(status_code=400, content={"detail": "Invalid filename"})

    # Only allow video file extensions
    allowed_extensions = {".mp4", ".webm", ".mov"}
    _, ext = os.path.splitext(safe_name)
    if ext.lower() not in allowed_extensions:
        return JSONResponse(status_code=400, content={"detail": "File type not allowed"})

    file_path = settings.MEDIA_DIR / safe_name
    # Resolve and verify the file is within MEDIA_DIR
    resolved = file_path.resolve()
    if not str(resolved).startswith(str(settings.MEDIA_DIR.resolve())):
        return JSONResponse(status_code=400, content={"detail": "Invalid path"})

    if not resolved.exists():
        return JSONResponse(status_code=404, content={"detail": "File not found"})
    return FileResponse(
        str(resolved),
        media_type="video/mp4",
        filename=safe_name,
    )


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "features": {
            "supabase": bool(settings.SUPABASE_DB_URL),
            "openrouter": bool(settings.OPENROUTER_API_KEY),
            "reddit": bool(settings.REDDIT_CLIENT_ID),
            "sora": bool(settings.OPENAI_API_KEY),
            "pexels": bool(settings.PEXELS_API_KEY),
            "elevenlabs": bool(settings.ELEVENLABS_API_KEY),
            "tts_free": True,  # edge-tts always available
        },
    }

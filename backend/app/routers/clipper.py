"""Auto video clipper endpoints."""

import os
import shutil

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Project, Video
from app.schemas import ClipperGenerateRequest
from app.services import caption_service, clipper_service, video_service
from app.tasks.task_manager import task_manager

router = APIRouter(prefix="/api/clipper", tags=["clipper"])


@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a long-form video for clipping."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    # Save uploaded file
    upload_path = str(settings.UPLOADS_DIR / file.filename)
    with open(upload_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Get video info
    info = clipper_service.get_video_info(upload_path)

    # Create project
    project = Project(
        name=f"Clip: {file.filename}",
        type="clipper",
        status="uploaded",
        config={
            "original_file": file.filename,
            "upload_path": upload_path,
            "video_info": info,
        },
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    return {
        "project_id": project.id,
        "filename": file.filename,
        "video_info": info,
    }


@router.post("/analyze/{project_id}")
async def analyze_video(
    project_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Analyze an uploaded video for best clip moments."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    upload_path = project.config.get("upload_path", "")
    if not os.path.exists(upload_path):
        raise HTTPException(status_code=404, detail="Video file not found")

    task_id = task_manager.create_task()
    project.task_id = task_id
    project.status = "analyzing"
    db.commit()

    background_tasks.add_task(
        _analyze_task,
        project_id=project.id,
        task_id=task_id,
        video_path=upload_path,
    )

    return {
        "project_id": project.id,
        "task_id": task_id,
        "status": "analyzing",
    }


async def _analyze_task(project_id: int, task_id: str, video_path: str):
    """Background: transcribe and find clip candidates."""
    from app.database import SessionLocal
    db = SessionLocal()

    try:
        task_manager.update_task(task_id, status="processing", progress=10, message="Transcribing audio...")

        # Transcribe
        words = caption_service.transcribe_audio_with_whisper(video_path, model_size="base")

        task_manager.update_task(task_id, progress=60, message="Finding best moments...")

        # Analyze for clips
        clips = clipper_service.analyze_transcript_for_clips(words)

        # Detect scene changes
        scenes = clipper_service.detect_scenes(video_path)

        task_manager.update_task(task_id, progress=90, message="Done analyzing")

        # Update project with results
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.config = {
                **project.config,
                "clips": clips,
                "scenes": [s["time"] for s in scenes],
                "transcript_words": len(words),
            }
            project.status = "analyzed"
            db.commit()

        task_manager.update_task(
            task_id,
            status="completed",
            progress=100,
            message=f"Found {len(clips)} potential clips",
            result={"clips": clips, "scene_count": len(scenes)},
        )
    except Exception as e:
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = "failed"
            project.error_message = str(e)
            db.commit()
        task_manager.update_task(task_id, status="failed", message=str(e))
    finally:
        db.close()


@router.post("/generate/{project_id}")
async def generate_clips(
    project_id: int,
    req: ClipperGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Generate clips from selected moments."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    upload_path = project.config.get("upload_path", "")
    if not os.path.exists(upload_path):
        raise HTTPException(status_code=404, detail="Video file not found")

    task_id = task_manager.create_task()
    project.task_id = task_id
    project.status = "processing"
    db.commit()

    background_tasks.add_task(
        _generate_clips_task,
        project_id=project.id,
        task_id=task_id,
        video_path=upload_path,
        clips=[c.model_dump() for c in req.clips],
        add_captions=req.add_captions,
        aspect_ratio=req.aspect_ratio,
    )

    return {
        "project_id": project.id,
        "task_id": task_id,
        "status": "processing",
        "clip_count": len(req.clips),
    }


async def _generate_clips_task(
    project_id: int,
    task_id: str,
    video_path: str,
    clips: list[dict],
    add_captions: bool,
    aspect_ratio: str,
):
    """Background: generate clip videos."""
    from app.database import SessionLocal
    db = SessionLocal()

    try:
        total = len(clips)
        resolution = (1080, 1920) if aspect_ratio == "9:16" else (1920, 1080)

        for i, clip_data in enumerate(clips):
            progress = int(((i) / total) * 90) + 5
            task_manager.update_task(
                task_id, status="processing", progress=progress,
                message=f"Generating clip {i+1}/{total}...",
            )

            output_path = video_service.create_clip(
                input_path=video_path,
                start=clip_data["start"],
                end=clip_data["end"],
                target_resolution=resolution,
            )

            duration = video_service.get_video_duration(output_path)

            video = Video(
                project_id=project_id,
                title=clip_data.get("title", f"Clip {i+1}"),
                file_path=os.path.basename(output_path),
                duration=duration,
                resolution=f"{resolution[0]}x{resolution[1]}",
                status="ready",
            )
            db.add(video)
            db.commit()

        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = "completed"
            db.commit()

        task_manager.update_task(
            task_id, status="completed", progress=100,
            message=f"Generated {total} clips!",
        )
    except Exception as e:
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = "failed"
            project.error_message = str(e)
            db.commit()
        task_manager.update_task(task_id, status="failed", message=str(e))
    finally:
        db.close()

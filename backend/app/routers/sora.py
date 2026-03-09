"""Sora AI video generation endpoints."""

import os

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project, Video
from app.schemas import SoraGenerateRequest
from app.services import sora_service, video_service
from app.tasks.task_manager import task_manager

router = APIRouter(prefix="/api/sora", tags=["sora"])


@router.post("/generate")
async def generate_sora_video(
    req: SoraGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Generate an AI video using OpenAI Sora."""
    # Create project
    project = Project(
        name=f"Sora: {req.prompt[:80]}",
        type="sora",
        status="processing",
        config={
            "prompt": req.prompt,
            "duration": req.duration,
            "aspect_ratio": req.aspect_ratio,
        },
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    task_id = task_manager.create_task()
    project.task_id = task_id
    db.commit()

    background_tasks.add_task(
        _generate_sora_task,
        project_id=project.id,
        task_id=task_id,
        prompt=req.prompt,
        duration=req.duration,
        aspect_ratio=req.aspect_ratio,
    )

    return {
        "project_id": project.id,
        "task_id": task_id,
        "status": "processing",
        "message": "Sora generation started",
    }


async def _generate_sora_task(
    project_id: int,
    task_id: str,
    prompt: str,
    duration: int,
    aspect_ratio: str,
):
    """Background task to generate a Sora video."""
    from app.database import SessionLocal
    db = SessionLocal()

    try:
        task_manager.update_task(task_id, status="processing", progress=20, message="Sending to Sora API...")

        result = await sora_service.generate_video(
            prompt=prompt,
            duration=duration,
            aspect_ratio=aspect_ratio,
        )

        if result["status"] == "error":
            raise Exception(result["error"])

        task_manager.update_task(task_id, progress=80, message="Processing video...")

        video_path = result["video_path"]
        vid_duration = video_service.get_video_duration(video_path)

        resolution = "1080x1920" if aspect_ratio == "9:16" else "1920x1080"

        video = Video(
            project_id=project_id,
            title=f"Sora: {prompt[:80]}",
            file_path=os.path.basename(video_path),
            duration=vid_duration,
            resolution=resolution,
            status="ready",
        )
        db.add(video)

        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = "completed"
        db.commit()

        task_manager.update_task(
            task_id,
            status="completed",
            progress=100,
            message="Video ready!",
            result={"video_id": video.id, "file_path": video.file_path},
        )

    except Exception as e:
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = "failed"
            project.error_message = str(e)
            db.commit()

        task_manager.update_task(task_id, status="failed", message=f"Error: {e}")
    finally:
        db.close()

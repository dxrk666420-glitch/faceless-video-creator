"""Reddit story video generation endpoints."""

import asyncio
import os

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Project, Video
from app.schemas import RedditGenerateRequest, RedditStory
from app.services import pexels_service, reddit_service, tts_service, video_service
from app.tasks.task_manager import task_manager

router = APIRouter(prefix="/api/reddit", tags=["reddit"])


@router.get("/voices")
async def list_voices():
    """List available TTS voices."""
    voices = await tts_service.get_available_voices()
    return voices


@router.get("/subreddits")
def list_subreddits():
    """List popular story subreddits."""
    return reddit_service.STORY_SUBREDDITS


@router.get("/search", response_model=list[RedditStory])
def search_stories(
    subreddit: str = "AskReddit",
    sort: str = "hot",
    limit: int = 20,
    time_filter: str = "week",
):
    """Search for stories on Reddit."""
    stories = reddit_service.search_stories(
        subreddit=subreddit,
        sort=sort,
        limit=limit,
        time_filter=time_filter,
    )
    return stories


@router.post("/generate")
async def generate_reddit_video(
    req: RedditGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Generate a faceless video from a Reddit story."""
    # Create project
    project = Project(
        name=req.story_title[:100],
        type="reddit",
        status="processing",
        config={
            "voice": req.voice,
            "background_category": req.background_category,
            "font_size": req.font_size,
        },
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # Create task for tracking
    task_id = task_manager.create_task()
    project.task_id = task_id
    db.commit()

    # Run generation in background
    background_tasks.add_task(
        _generate_video_task,
        project_id=project.id,
        task_id=task_id,
        story_title=req.story_title,
        story_text=req.story_text,
        voice=req.voice,
        background_category=req.background_category,
        font_size=req.font_size,
        font_color=req.font_color,
        highlight_color=req.highlight_color,
    )

    return {
        "project_id": project.id,
        "task_id": task_id,
        "status": "processing",
        "message": "Video generation started",
    }


async def _generate_video_task(
    project_id: int,
    task_id: str,
    story_title: str,
    story_text: str,
    voice: str,
    background_category: str,
    font_size: int,
    font_color: str,
    highlight_color: str,
):
    """Background task to generate a Reddit story video."""
    db = next(iter([__import__("app.database", fromlist=["SessionLocal"]).SessionLocal()]))

    try:
        task_manager.update_task(task_id, status="processing", progress=10, message="Generating narration...")

        # 1. Generate TTS with word timestamps
        audio_path, word_timestamps = await tts_service.generate_tts_with_timestamps(
            text=story_text,
            voice=voice,
        )

        task_manager.update_task(task_id, progress=30, message="Fetching background video...")

        # 2. Download background video
        background_path = await pexels_service.download_background_video(
            category=background_category,
        )

        task_manager.update_task(task_id, progress=50, message="Composing video...")

        # 3. Compose final video
        output_path = video_service.compose_reddit_video(
            audio_path=audio_path,
            word_timestamps=word_timestamps,
            background_path=background_path,
            title=story_title,
            font_size=font_size,
            font_color=font_color,
            highlight_color=highlight_color,
        )

        task_manager.update_task(task_id, progress=90, message="Finalizing...")

        # 4. Get video duration
        duration = video_service.get_video_duration(output_path)

        # 5. Save video record
        video = Video(
            project_id=project_id,
            title=story_title,
            file_path=os.path.basename(output_path),
            duration=duration,
            resolution="1080x1920",
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

        # Cleanup temp files
        if os.path.exists(audio_path):
            os.unlink(audio_path)
        if background_path and os.path.exists(background_path):
            os.unlink(background_path)

    except Exception as e:
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = "failed"
            project.error_message = str(e)
            db.commit()

        task_manager.update_task(
            task_id,
            status="failed",
            message=f"Error: {e}",
        )
    finally:
        db.close()

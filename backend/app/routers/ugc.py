"""AI UGC creator endpoints."""

import os

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project, Video
from app.schemas import UGCGenerateRequest
from app.services import ugc_service, video_service
from app.tasks.task_manager import task_manager

router = APIRouter(prefix="/api/ugc", tags=["ugc"])


@router.get("/templates")
def list_templates():
    """List available UGC video templates."""
    return ugc_service.get_templates()


@router.post("/generate")
async def generate_ugc_video(
    req: UGCGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Generate a UGC-style video for a brand."""
    project = Project(
        name=f"UGC: {req.product_name}",
        type="ugc",
        status="processing",
        config={
            "product_name": req.product_name,
            "script": req.script,
            "voice": req.voice,
            "style": req.style,
            "stock_keywords": req.stock_keywords,
            "brand_color": req.brand_color,
        },
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    task_id = task_manager.create_task()
    project.task_id = task_id
    db.commit()

    background_tasks.add_task(
        _generate_ugc_task,
        project_id=project.id,
        task_id=task_id,
        product_name=req.product_name,
        script=req.script,
        voice=req.voice,
        style=req.style,
        stock_keywords=req.stock_keywords,
        brand_color=req.brand_color,
    )

    return {
        "project_id": project.id,
        "task_id": task_id,
        "status": "processing",
    }


async def _generate_ugc_task(
    project_id: int,
    task_id: str,
    product_name: str,
    script: str,
    voice: str,
    style: str,
    stock_keywords: list[str],
    brand_color: str,
):
    """Background: generate UGC video."""
    from app.database import SessionLocal
    db = SessionLocal()

    try:
        task_manager.update_task(task_id, status="processing", progress=10, message="Creating UGC video...")

        output_path = await ugc_service.generate_ugc_video(
            product_name=product_name,
            script=script,
            voice=voice,
            style=style,
            stock_keywords=stock_keywords,
            brand_color=brand_color,
        )

        task_manager.update_task(task_id, progress=90, message="Finalizing...")

        duration = video_service.get_video_duration(output_path)

        video = Video(
            project_id=project_id,
            title=f"UGC: {product_name}",
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
            task_id, status="completed", progress=100,
            message="UGC video ready!",
            result={"video_id": video.id, "file_path": video.file_path},
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

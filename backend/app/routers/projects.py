"""Project CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project, Video
from app.schemas import ProjectCreate, ProjectList, ProjectOut

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectList])
def list_projects(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.created_at.desc()).offset(skip).limit(limit).all()
    result = []
    for p in projects:
        video_count = db.query(func.count(Video.id)).filter(Video.project_id == p.id).scalar()
        result.append(ProjectList(
            id=p.id,
            name=p.name,
            type=p.type,
            status=p.status,
            created_at=p.created_at,
            updated_at=p.updated_at,
            video_count=video_count,
        ))
    return result


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("", response_model=ProjectOut)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(name=data.name, type=data.type, config=data.config)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return {"ok": True}

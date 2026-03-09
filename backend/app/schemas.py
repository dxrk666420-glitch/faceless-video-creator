from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# --- Project schemas ---
class ProjectBase(BaseModel):
    name: str
    type: str
    config: dict[str, Any] = {}


class ProjectCreate(ProjectBase):
    pass


class VideoOut(BaseModel):
    id: int
    project_id: int
    title: str
    file_path: str
    thumbnail_path: str | None = None
    duration: float | None = None
    resolution: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectOut(BaseModel):
    id: int
    name: str
    type: str
    status: str
    config: dict[str, Any]
    error_message: str | None = None
    task_id: str | None = None
    created_at: datetime
    updated_at: datetime
    videos: list[VideoOut] = []

    model_config = {"from_attributes": True}


class ProjectList(BaseModel):
    id: int
    name: str
    type: str
    status: str
    created_at: datetime
    updated_at: datetime
    video_count: int = 0

    model_config = {"from_attributes": True}


# --- Reddit schemas ---
class RedditStory(BaseModel):
    id: str
    title: str
    selftext: str
    subreddit: str
    score: int
    url: str
    num_comments: int
    author: str
    created_utc: float


class AIStoryRequest(BaseModel):
    topic: str = Field("", max_length=500)
    style: str = Field("reddit_tifu", max_length=50)
    custom_prompt: str = Field("", max_length=2000)


class RedditGenerateRequest(BaseModel):
    story_title: str = Field(..., min_length=1, max_length=500)
    story_text: str = Field(..., min_length=1, max_length=50000)
    voice: str = Field("en-US-ChristopherNeural", max_length=100)
    background_category: str = Field("satisfying", max_length=50)
    font_size: int = Field(70, ge=20, le=200)
    font_color: str = Field("#FFFFFF", pattern=r'^#[0-9A-Fa-f]{6}$')
    highlight_color: str = Field("#FFD700", pattern=r'^#[0-9A-Fa-f]{6}$')


# --- Sora schemas ---
class SoraGenerateRequest(BaseModel):
    prompt: str
    duration: int = 5  # seconds
    aspect_ratio: str = "9:16"  # 9:16, 16:9, 1:1


# --- Clipper schemas ---
class ClipSegment(BaseModel):
    start: float
    end: float
    title: str = ""
    score: float = 0.0
    text: str = ""


class ClipperGenerateRequest(BaseModel):
    clips: list[ClipSegment]
    add_captions: bool = True
    aspect_ratio: str = "9:16"


# --- UGC schemas ---
class UGCGenerateRequest(BaseModel):
    product_name: str
    script: str
    voice: str = "en-US-JennyNeural"
    style: str = "testimonial"  # testimonial | review | showcase
    stock_keywords: list[str] = []
    brand_color: str = "#FF6B35"


# --- Job schemas ---
class JobStatus(BaseModel):
    task_id: str
    status: str  # pending | processing | completed | failed
    progress: float = 0.0  # 0-100
    message: str = ""
    result: dict[str, Any] | None = None

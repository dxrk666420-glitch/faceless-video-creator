"""Pexels stock footage service for background videos."""

import random
from pathlib import Path

import httpx

from app.config import settings

PEXELS_BASE_URL = "https://api.pexels.com"

# Search queries mapped to background categories
BACKGROUND_QUERIES = {
    "minecraft": ["minecraft gameplay", "block game parkour", "pixel art gaming"],
    "subway_surfers": ["subway runner game", "endless runner", "mobile game gameplay"],
    "satisfying": [
        "satisfying soap cutting",
        "kinetic sand",
        "paint mixing satisfying",
        "slime asmr",
        "calligraphy writing",
        "pottery wheel",
        "pressure washing satisfying",
    ],
    "nature": ["aerial nature drone", "ocean waves", "forest timelapse"],
    "abstract": ["abstract colorful motion", "neon lights", "liquid motion art"],
}


async def search_videos(
    query: str,
    per_page: int = 10,
    orientation: str = "portrait",
) -> list[dict]:
    """Search Pexels for videos."""
    if not settings.PEXELS_API_KEY:
        return []

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{PEXELS_BASE_URL}/videos/search",
            params={
                "query": query,
                "per_page": per_page,
                "orientation": orientation,
            },
            headers={"Authorization": settings.PEXELS_API_KEY},
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()

    return [
        {
            "id": v["id"],
            "url": v["url"],
            "duration": v["duration"],
            "width": v["width"],
            "height": v["height"],
            "video_files": [
                {
                    "id": vf["id"],
                    "quality": vf.get("quality", ""),
                    "width": vf.get("width", 0),
                    "height": vf.get("height", 0),
                    "link": vf["link"],
                }
                for vf in v.get("video_files", [])
            ],
        }
        for v in data.get("videos", [])
    ]


async def download_background_video(
    category: str = "satisfying",
    output_path: str | None = None,
    min_duration: int = 30,
) -> str | None:
    """Download a background video from Pexels for a given category.

    Returns the path to the downloaded video, or None if unavailable.
    """
    queries = BACKGROUND_QUERIES.get(category, BACKGROUND_QUERIES["satisfying"])
    query = random.choice(queries)

    videos = await search_videos(query, per_page=15, orientation="portrait")

    # Filter for videos long enough
    suitable = [v for v in videos if v["duration"] >= min_duration]
    if not suitable:
        suitable = videos  # Use whatever we have

    if not suitable:
        return None

    video = random.choice(suitable)

    # Find best quality file (prefer HD)
    video_files = sorted(
        video["video_files"],
        key=lambda x: x.get("height", 0),
        reverse=True,
    )
    if not video_files:
        return None

    download_url = video_files[0]["link"]

    if output_path is None:
        output_path = str(settings.MEDIA_DIR / f"bg_{video['id']}.mp4")

    # Download the video
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(download_url, timeout=120.0)
        response.raise_for_status()
        with open(output_path, "wb") as f:
            f.write(response.content)

    return output_path

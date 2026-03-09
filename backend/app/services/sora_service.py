"""OpenAI Sora video generation service."""

import os

import httpx
from openai import AsyncOpenAI

from app.config import settings


def get_openai_client() -> AsyncOpenAI | None:
    """Create an AsyncOpenAI client. Returns None if API key not configured."""
    if not settings.OPENAI_API_KEY:
        return None
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def generate_video(
    prompt: str,
    duration: int = 5,
    aspect_ratio: str = "9:16",
    output_path: str | None = None,
) -> dict:
    """Generate a video using OpenAI's Sora API.

    Returns: {"status": str, "video_path": str | None, "error": str | None}
    """
    client = get_openai_client()
    if client is None:
        return {
            "status": "error",
            "video_path": None,
            "error": "OpenAI API key not configured. Set OPENAI_API_KEY in .env",
        }

    if output_path is None:
        output_path = str(settings.MEDIA_DIR / f"sora_{os.urandom(4).hex()}.mp4")

    try:
        # Use the OpenAI API to generate video
        # Sora is accessed through the responses API
        response = await client.responses.create(
            model="sora",
            input=prompt,
            tools=[{
                "type": "video_generation",
                "duration": duration,
                "aspect_ratio": aspect_ratio,
            }],
        )

        # Extract video URL from response
        video_url = None
        for output in response.output:
            if hasattr(output, "video_url"):
                video_url = output.video_url
                break

        if not video_url:
            return {
                "status": "error",
                "video_path": None,
                "error": "No video URL in response",
            }

        # Download the video
        async with httpx.AsyncClient(follow_redirects=True) as http_client:
            resp = await http_client.get(video_url, timeout=120.0)
            resp.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(resp.content)

        return {
            "status": "completed",
            "video_path": output_path,
            "error": None,
        }

    except Exception as e:
        return {
            "status": "error",
            "video_path": None,
            "error": str(e),
        }

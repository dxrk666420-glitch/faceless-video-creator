"""Text-to-speech service using edge-tts (free) with ElevenLabs fallback."""

import asyncio
import io
import tempfile
from pathlib import Path

import edge_tts
import httpx

from app.config import settings


async def get_available_voices() -> list[dict]:
    """Get all available edge-tts voices."""
    voices = await edge_tts.list_voices()
    # Filter to English voices and format nicely
    result = []
    for v in voices:
        result.append({
            "id": v["ShortName"],
            "name": v["FriendlyName"],
            "gender": v["Gender"],
            "locale": v["Locale"],
        })
    # Sort: English first, then by name
    result.sort(key=lambda x: (0 if x["locale"].startswith("en") else 1, x["name"]))
    return result


async def generate_tts_audio(text: str, voice: str = "en-US-ChristopherNeural", output_path: str | None = None) -> str:
    """Generate TTS audio file from text using edge-tts.

    Returns the path to the generated audio file (.mp3).
    """
    if output_path is None:
        output_path = str(settings.MEDIA_DIR / f"tts_{id(text) & 0xFFFFFFFF:08x}.mp3")

    # Try ElevenLabs first if API key is set
    if settings.ELEVENLABS_API_KEY:
        try:
            return await _generate_elevenlabs(text, output_path)
        except Exception:
            pass  # Fall through to edge-tts

    # Use edge-tts (free, no API key needed)
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)
    return output_path


async def generate_tts_with_timestamps(
    text: str,
    voice: str = "en-US-ChristopherNeural",
    output_path: str | None = None,
) -> tuple[str, list[dict]]:
    """Generate TTS audio and return word-level timestamps.

    Returns: (audio_path, word_timestamps)
    where word_timestamps is a list of {"text": str, "start": float, "end": float}
    """
    if output_path is None:
        output_path = str(settings.MEDIA_DIR / f"tts_{id(text) & 0xFFFFFFFF:08x}.mp3")

    communicate = edge_tts.Communicate(text, voice)
    word_timestamps = []

    with open(output_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                word_timestamps.append({
                    "text": chunk["text"],
                    "start": chunk["offset"] / 10_000_000,  # Convert 100ns units to seconds
                    "end": (chunk["offset"] + chunk["duration"]) / 10_000_000,
                })

    return output_path, word_timestamps


async def _generate_elevenlabs(text: str, output_path: str) -> str:
    """Generate TTS using ElevenLabs API."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM",
            headers={
                "xi-api-key": settings.ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
            },
            timeout=60.0,
        )
        response.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(response.content)

    return output_path

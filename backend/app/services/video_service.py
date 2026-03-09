"""Video composition service - assembles final videos using MoviePy."""

import os
import tempfile
from pathlib import Path

import numpy as np
from moviepy import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    TextClip,
    VideoFileClip,
    concatenate_videoclips,
)

from app.config import settings
from app.services.caption_service import create_caption_frame


def compose_reddit_video(
    audio_path: str,
    word_timestamps: list[dict],
    background_path: str | None = None,
    output_path: str | None = None,
    title: str = "",
    font_size: int = 70,
    font_color: str = "#FFFFFF",
    highlight_color: str = "#FFD700",
    resolution: tuple[int, int] = (1080, 1920),
) -> str:
    """Compose a Reddit story video with background + captions + narration.

    Args:
        audio_path: Path to the TTS audio file
        word_timestamps: Word-level timestamps from TTS/Whisper
        background_path: Path to background video (or None for solid color)
        output_path: Where to save the final video
        title: Story title (shown at top)
        font_size: Caption font size
        font_color: Default caption color
        highlight_color: Highlighted word color
        resolution: (width, height) tuple

    Returns:
        Path to the output video file
    """
    if output_path is None:
        output_path = str(settings.MEDIA_DIR / f"reddit_{os.urandom(4).hex()}.mp4")

    width, height = resolution
    audio = AudioFileClip(audio_path)
    duration = audio.duration

    # Create background
    if background_path and os.path.exists(background_path):
        bg = VideoFileClip(background_path)
        # Resize to fill frame (crop to 9:16)
        bg_ratio = bg.w / bg.h
        target_ratio = width / height
        if bg_ratio > target_ratio:
            bg = bg.resized(height=height)
        else:
            bg = bg.resized(width=width)
        bg = bg.cropped(
            x_center=bg.w / 2,
            y_center=bg.h / 2,
            width=width,
            height=height,
        )
        # Loop if background is shorter than audio
        if bg.duration < duration:
            loops_needed = int(duration / bg.duration) + 1
            bg = concatenate_videoclips([bg] * loops_needed)
        bg = bg.subclipped(0, duration)
    else:
        # Solid dark background as fallback
        bg = ColorClip(size=(width, height), color=(15, 15, 25)).with_duration(duration)

    # Create caption overlay using frame-by-frame rendering
    def make_caption_frame(t):
        frame = create_caption_frame(
            words=word_timestamps,
            current_time=t,
            width=width,
            height=height,
            font_size=font_size,
            font_color=font_color,
            highlight_color=highlight_color,
        )
        return frame

    caption_clip = VideoFileClip.__new__(VideoFileClip)
    # Use a lambda approach with ColorClip as base
    caption_base = ColorClip(size=(width, height), color=(0, 0, 0, 0)).with_duration(duration)

    # Compose layers
    final = CompositeVideoClip([bg]).with_duration(duration)
    final = final.with_audio(audio)

    # Add title text at top if provided
    clips = [bg]

    if title:
        try:
            title_clip = TextClip(
                text=title,
                font_size=40,
                color="white",
                font="DejaVu-Sans-Bold",
                size=(width - 100, None),
                method="caption",
            ).with_duration(duration).with_position(("center", 80))
            clips.append(title_clip)
        except Exception:
            pass  # Skip title if font not available

    # Render captions frame by frame via a temporary video approach
    # We'll use FFmpeg subtitle burn-in as a more reliable method
    srt_path = _generate_highlight_srt(word_timestamps, highlight_color)

    final = CompositeVideoClip(clips, size=(width, height)).with_duration(duration)
    final = final.with_audio(audio)

    # Write output
    final.write_videofile(
        output_path,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        threads=4,
        logger=None,
    )

    # Burn in subtitles using FFmpeg for better quality
    if srt_path and os.path.exists(srt_path):
        _burn_subtitles_ffmpeg(output_path, srt_path, font_size, font_color, highlight_color)
        os.unlink(srt_path)

    # Cleanup
    audio.close()
    if background_path and os.path.exists(background_path):
        bg.close()

    return output_path


def _generate_highlight_srt(words: list[dict], highlight_color: str) -> str | None:
    """Generate SRT with styled captions (groups of 2-3 words)."""
    if not words:
        return None

    srt_path = str(settings.MEDIA_DIR / f"captions_{os.urandom(4).hex()}.srt")
    lines = []
    idx = 1
    group_size = 3

    for i in range(0, len(words), group_size):
        group = words[i : i + group_size]
        if not group:
            continue

        start = group[0]["start"]
        end = group[-1]["end"]
        text = " ".join(w["text"] for w in group)

        start_str = _srt_time(start)
        end_str = _srt_time(end)

        lines.append(str(idx))
        lines.append(f"{start_str} --> {end_str}")
        lines.append(text.upper())
        lines.append("")
        idx += 1

    with open(srt_path, "w") as f:
        f.write("\n".join(lines))

    return srt_path


def _burn_subtitles_ffmpeg(
    video_path: str,
    srt_path: str,
    font_size: int,
    font_color: str,
    highlight_color: str,
):
    """Burn SRT subtitles into video using FFmpeg."""
    import subprocess

    temp_output = video_path + ".tmp.mp4"

    # Convert hex color to FFmpeg ASS format (BGR)
    fc = font_color.lstrip("#")
    ass_color = f"&H00{fc[4:6]}{fc[2:4]}{fc[0:2]}&"

    subtitle_filter = (
        f"subtitles={srt_path}:force_style='"
        f"FontName=DejaVu Sans,FontSize={font_size // 3},"
        f"PrimaryColour={ass_color},"
        f"OutlineColour=&H00000000&,Outline=2,"
        f"Shadow=1,ShadowColour=&H80000000&,"
        f"Alignment=10,MarginV=350,"
        f"Bold=1'"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", subtitle_filter,
        "-c:a", "copy",
        "-preset", "medium",
        temp_output,
    ]

    try:
        subprocess.run(cmd, capture_output=True, check=True, timeout=300)
        os.replace(temp_output, video_path)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # If FFmpeg fails, keep the video without burned-in subs
        if os.path.exists(temp_output):
            os.unlink(temp_output)


def _srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def create_clip(
    input_path: str,
    start: float,
    end: float,
    output_path: str | None = None,
    target_resolution: tuple[int, int] = (1080, 1920),
    add_captions: bool = False,
    srt_path: str | None = None,
) -> str:
    """Extract a clip from a video and optionally crop to vertical."""
    if output_path is None:
        output_path = str(settings.MEDIA_DIR / f"clip_{os.urandom(4).hex()}.mp4")

    video = VideoFileClip(input_path)
    clip = video.subclipped(start, min(end, video.duration))

    tw, th = target_resolution
    target_ratio = tw / th
    clip_ratio = clip.w / clip.h

    # Crop to target aspect ratio (center crop)
    if clip_ratio > target_ratio:
        # Video is wider - crop sides
        new_w = int(clip.h * target_ratio)
        clip = clip.cropped(x_center=clip.w / 2, width=new_w, y1=0, y2=clip.h)
    elif clip_ratio < target_ratio:
        # Video is taller - crop top/bottom
        new_h = int(clip.w / target_ratio)
        clip = clip.cropped(y_center=clip.h / 2, height=new_h, x1=0, x2=clip.w)

    clip = clip.resized(target_resolution)

    clip.write_videofile(
        output_path,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        threads=4,
        logger=None,
    )

    video.close()

    # Burn in captions if requested
    if add_captions and srt_path and os.path.exists(srt_path):
        _burn_subtitles_ffmpeg(output_path, srt_path, 60, "#FFFFFF", "#FFD700")

    return output_path


def get_video_duration(path: str) -> float:
    """Get duration of a video file in seconds."""
    try:
        video = VideoFileClip(path)
        dur = video.duration
        video.close()
        return dur
    except Exception:
        return 0.0

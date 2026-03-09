"""Auto video clipper service - detects best moments in long-form video."""

import json
import os
import subprocess
from pathlib import Path

from app.config import settings


def detect_scenes(video_path: str, threshold: float = 30.0) -> list[dict]:
    """Detect scene changes in a video using FFmpeg.

    Returns list of {"time": float, "score": float} for each scene change.
    """
    cmd = [
        "ffmpeg", "-i", video_path,
        "-filter:v", f"select='gt(scene,{threshold / 100})',showinfo",
        "-f", "null", "-",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        scenes = []
        for line in result.stderr.split("\n"):
            if "pts_time:" in line:
                parts = line.split("pts_time:")
                if len(parts) > 1:
                    time_str = parts[1].split()[0]
                    try:
                        scenes.append({"time": float(time_str), "score": threshold})
                    except ValueError:
                        pass
        return scenes
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def analyze_transcript_for_clips(
    words: list[dict],
    min_clip_duration: float = 15.0,
    max_clip_duration: float = 60.0,
    target_clips: int = 5,
) -> list[dict]:
    """Analyze word-level transcript to find the best clip candidates.

    Uses simple heuristics:
    - Sentence boundaries (pause detection)
    - Word density (more words = more interesting)
    - Natural speech pauses as clip boundaries

    Returns list of {"start": float, "end": float, "text": str, "score": float}
    """
    if not words:
        return []

    # Find natural pause points (gaps > 0.5s between words)
    pause_threshold = 0.5
    pause_points = [0.0]
    for i in range(1, len(words)):
        gap = words[i]["start"] - words[i - 1]["end"]
        if gap > pause_threshold:
            pause_points.append(words[i]["start"])
    pause_points.append(words[-1]["end"])

    # Build candidate segments from pause points
    candidates = []
    for i in range(len(pause_points) - 1):
        for j in range(i + 1, len(pause_points)):
            start = pause_points[i]
            end = pause_points[j]
            duration = end - start

            if duration < min_clip_duration:
                continue
            if duration > max_clip_duration:
                break

            # Count words in this segment
            segment_words = [w for w in words if w["start"] >= start and w["end"] <= end]
            if not segment_words:
                continue

            # Score: words per second (higher = more content-dense)
            word_density = len(segment_words) / duration
            text = " ".join(w["text"] for w in segment_words)

            candidates.append({
                "start": round(start, 2),
                "end": round(end, 2),
                "title": text[:80] + "..." if len(text) > 80 else text,
                "text": text,
                "score": round(word_density, 2),
            })

    # Sort by score and return top candidates
    candidates.sort(key=lambda x: x["score"], reverse=True)

    # Remove overlapping clips
    selected = []
    for candidate in candidates:
        overlaps = any(
            not (candidate["end"] <= s["start"] or candidate["start"] >= s["end"])
            for s in selected
        )
        if not overlaps:
            selected.append(candidate)
        if len(selected) >= target_clips:
            break

    # Sort by start time
    selected.sort(key=lambda x: x["start"])
    return selected


def get_video_info(video_path: str) -> dict:
    """Get video metadata using FFprobe."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams",
        video_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        data = json.loads(result.stdout)
        fmt = data.get("format", {})
        video_stream = next(
            (s for s in data.get("streams", []) if s.get("codec_type") == "video"),
            {},
        )
        return {
            "duration": float(fmt.get("duration", 0)),
            "width": int(video_stream.get("width", 0)),
            "height": int(video_stream.get("height", 0)),
            "codec": video_stream.get("codec_name", ""),
            "fps": _parse_fps(video_stream.get("r_frame_rate", "30/1")),
            "size_mb": round(int(fmt.get("size", 0)) / (1024 * 1024), 2),
        }
    except Exception:
        return {"duration": 0, "width": 0, "height": 0, "codec": "", "fps": 30, "size_mb": 0}


def _parse_fps(fps_str: str) -> float:
    try:
        if "/" in fps_str:
            num, den = fps_str.split("/")
            return round(int(num) / int(den), 2)
        return float(fps_str)
    except (ValueError, ZeroDivisionError):
        return 30.0

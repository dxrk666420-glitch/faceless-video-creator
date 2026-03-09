"""Caption service - generates word-by-word highlight captions for videos."""

import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def create_caption_frame(
    words: list[dict],
    current_time: float,
    width: int = 1080,
    height: int = 1920,
    font_size: int = 70,
    font_color: str = "#FFFFFF",
    highlight_color: str = "#FFD700",
    words_per_group: int = 3,
) -> np.ndarray:
    """Create a transparent caption frame with word-by-word highlighting.

    Args:
        words: List of {"text": str, "start": float, "end": float}
        current_time: Current timestamp in seconds
        width/height: Frame dimensions
        font_size: Caption font size
        font_color: Default text color
        highlight_color: Color for currently spoken word
        words_per_group: How many words to show at once

    Returns:
        RGBA numpy array (transparent background with text)
    """
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Try to load a bold font, fall back to default
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except (IOError, OSError):
        try:
            font = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf", font_size)
        except (IOError, OSError):
            font = ImageFont.load_default()

    # Find which group of words to display based on current time
    if not words:
        return np.array(img)

    # Find current word index
    current_idx = -1
    for i, w in enumerate(words):
        if w["start"] <= current_time <= w["end"]:
            current_idx = i
            break
        elif w["start"] > current_time:
            break
        current_idx = i

    if current_idx < 0:
        return np.array(img)

    # Determine which group to show (groups of words_per_group)
    group_start = (current_idx // words_per_group) * words_per_group
    group_end = min(group_start + words_per_group, len(words))
    group_words = words[group_start:group_end]

    if not group_words:
        return np.array(img)

    # Calculate vertical center position (slightly above center)
    y_center = int(height * 0.45)

    # Draw each word
    total_text = " ".join(w["text"] for w in group_words)
    bbox = draw.textbbox((0, 0), total_text, font=font)
    total_width = bbox[2] - bbox[0]

    # Start x position to center the group
    x = (width - total_width) // 2
    y = y_center

    # Draw text shadow for readability
    shadow_offset = 3
    for w in group_words:
        word_text = w["text"]
        is_current = w["start"] <= current_time <= w["end"]

        # Shadow
        draw.text((x + shadow_offset, y + shadow_offset), word_text, font=font, fill=(0, 0, 0, 200))

        # Main text
        color = highlight_color if is_current else font_color
        draw.text((x, y), word_text, font=font, fill=color)

        # Advance x
        word_bbox = draw.textbbox((0, 0), word_text + " ", font=font)
        x += word_bbox[2] - word_bbox[0]

    return np.array(img)


def transcribe_audio_with_whisper(audio_path: str, model_size: str = "base") -> list[dict]:
    """Transcribe audio file and return word-level timestamps.

    Uses OpenAI Whisper for speech-to-text with word timing.

    Returns: list of {"text": str, "start": float, "end": float}
    """
    import whisper

    model = whisper.load_model(model_size)
    result = model.transcribe(
        audio_path,
        word_timestamps=True,
        verbose=False,
    )

    words = []
    for segment in result.get("segments", []):
        for word_info in segment.get("words", []):
            words.append({
                "text": word_info["word"].strip(),
                "start": word_info["start"],
                "end": word_info["end"],
            })

    return words


def generate_srt(words: list[dict], words_per_line: int = 5) -> str:
    """Generate SRT subtitle file content from word timestamps."""
    lines = []
    idx = 1

    for i in range(0, len(words), words_per_line):
        group = words[i : i + words_per_line]
        if not group:
            continue

        start = group[0]["start"]
        end = group[-1]["end"]
        text = " ".join(w["text"] for w in group)

        start_str = _seconds_to_srt_time(start)
        end_str = _seconds_to_srt_time(end)

        lines.append(f"{idx}")
        lines.append(f"{start_str} --> {end_str}")
        lines.append(text)
        lines.append("")
        idx += 1

    return "\n".join(lines)


def _seconds_to_srt_time(seconds: float) -> str:
    """Convert seconds to SRT timestamp format: HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

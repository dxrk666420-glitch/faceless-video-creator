"""AI UGC (User Generated Content) creator service for brands."""

import os
from pathlib import Path

from app.config import settings
from app.services import pexels_service, tts_service, video_service


# UGC video templates
TEMPLATES = {
    "testimonial": {
        "name": "Customer Testimonial",
        "description": "A customer sharing their experience with a product",
        "script_template": (
            "I've been using {product} for a few weeks now and I have to tell you, "
            "it completely changed my routine. At first I was skeptical, but after seeing "
            "the results, I'm a believer. If you're on the fence, just try it. "
            "You won't regret it."
        ),
        "stock_keywords": ["person talking", "lifestyle", "happy customer"],
        "voice": "en-US-JennyNeural",
    },
    "review": {
        "name": "Product Review",
        "description": "An honest product review highlighting features and benefits",
        "script_template": (
            "Let me give you my honest review of {product}. "
            "The build quality is impressive and it does exactly what they promise. "
            "The best feature in my opinion is the ease of use. "
            "Is it worth the price? Absolutely. I'd rate it a solid 9 out of 10."
        ),
        "stock_keywords": ["product review", "unboxing", "close up hands"],
        "voice": "en-US-GuyNeural",
    },
    "showcase": {
        "name": "Product Showcase",
        "description": "A quick showcase of the product's key features",
        "script_template": (
            "Check this out. This is {product} and it's about to become your new favorite thing. "
            "Look at this design. Clean, minimal, functional. "
            "It works exactly how you'd expect it to, maybe even better. "
            "Link in bio if you want one."
        ),
        "stock_keywords": ["product showcase", "minimal aesthetic", "modern design"],
        "voice": "en-US-AriaNeural",
    },
    "problem_solution": {
        "name": "Problem-Solution",
        "description": "Present a common problem and show the product as the solution",
        "script_template": (
            "You know that annoying problem where you just can't seem to find a good solution? "
            "I tried everything until I found {product}. "
            "It solved the issue in minutes and I haven't looked back since. "
            "Seriously, where has this been all my life?"
        ),
        "stock_keywords": ["frustrated person", "solution", "relief happy"],
        "voice": "en-US-SaraNeural",
    },
}


def get_templates() -> list[dict]:
    """Return available UGC templates."""
    return [
        {
            "id": key,
            "name": tpl["name"],
            "description": tpl["description"],
            "script_template": tpl["script_template"],
            "voice": tpl["voice"],
        }
        for key, tpl in TEMPLATES.items()
    ]


async def generate_ugc_video(
    product_name: str,
    script: str,
    voice: str = "en-US-JennyNeural",
    style: str = "testimonial",
    stock_keywords: list[str] | None = None,
    brand_color: str = "#FF6B35",
    output_path: str | None = None,
) -> str:
    """Generate a UGC-style video for a brand.

    Pipeline:
    1. Generate TTS narration from script
    2. Get word timestamps
    3. Fetch stock footage based on keywords
    4. Compose video with captions

    Returns path to the output video.
    """
    if output_path is None:
        output_path = str(settings.MEDIA_DIR / f"ugc_{os.urandom(4).hex()}.mp4")

    # Fill in product name in script if template placeholder exists
    script = script.replace("{product}", product_name)

    # 1. Generate TTS with word timestamps
    audio_path, word_timestamps = await tts_service.generate_tts_with_timestamps(
        text=script,
        voice=voice,
    )

    # 2. Try to fetch background stock footage
    keywords = stock_keywords or TEMPLATES.get(style, {}).get("stock_keywords", ["lifestyle"])
    background_path = None
    for keyword in keywords:
        background_path = await pexels_service.download_background_video(
            category="nature",  # Use nature as general fallback
            output_path=str(settings.MEDIA_DIR / f"ugc_bg_{os.urandom(4).hex()}.mp4"),
        )
        if background_path:
            break

    # 3. Compose video
    result = video_service.compose_reddit_video(
        audio_path=audio_path,
        word_timestamps=word_timestamps,
        background_path=background_path,
        output_path=output_path,
        title=product_name,
        font_size=65,
        font_color="#FFFFFF",
        highlight_color=brand_color,
    )

    # Cleanup temp files
    if os.path.exists(audio_path):
        os.unlink(audio_path)
    if background_path and os.path.exists(background_path):
        os.unlink(background_path)

    return result

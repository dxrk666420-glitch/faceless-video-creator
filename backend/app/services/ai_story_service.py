"""AI story generation service using OpenRouter API."""

import httpx

from app.config import settings

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Story generation prompts for different styles
STORY_STYLES = {
    "reddit_tifu": {
        "name": "TIFU (Today I F***ed Up)",
        "system": "You are a creative writer who writes viral Reddit TIFU stories. Write in first person, casual Reddit style. The story should be funny, relatable, and have a satisfying punchline. Keep it between 100-200 words for a short-form video.",
    },
    "askreddit": {
        "name": "AskReddit Story",
        "system": "You are a creative writer who writes compelling AskReddit-style personal stories. Write in first person, conversational tone. The story should be surprising, emotional, or mind-blowing. Keep it between 100-200 words for a short-form video.",
    },
    "nosleep": {
        "name": "Horror / NoSleep",
        "system": "You are a creative horror writer who writes viral Reddit NoSleep stories. Write in first person, building tension gradually. The story should be creepy and have a chilling twist ending. Keep it between 100-200 words for a short-form video.",
    },
    "revenge": {
        "name": "Petty/Pro Revenge",
        "system": "You are a creative writer who writes satisfying revenge stories in Reddit style. Write in first person, building up the injustice then delivering a clever payoff. Keep it between 100-200 words for a short-form video.",
    },
    "wholesome": {
        "name": "Wholesome / Heartwarming",
        "system": "You are a creative writer who writes heartwarming, wholesome stories in Reddit style. Write in first person, building emotional connection. The story should make people smile or tear up. Keep it between 100-200 words for a short-form video.",
    },
    "mystery": {
        "name": "Unexplained / Mystery",
        "system": "You are a creative writer who writes mysterious, unexplainable true-story-style Reddit posts. Write in first person, casual tone. The story should leave the reader with chills and unanswered questions. Keep it between 100-200 words for a short-form video.",
    },
}


def get_story_styles() -> list[dict]:
    """Return available AI story generation styles."""
    return [{"id": k, "name": v["name"]} for k, v in STORY_STYLES.items()]


async def generate_story(
    topic: str = "",
    style: str = "reddit_tifu",
    custom_prompt: str = "",
) -> dict:
    """Generate a story using OpenRouter API.

    Args:
        topic: Optional topic hint (e.g. "about a job interview gone wrong")
        style: One of the STORY_STYLES keys
        custom_prompt: If provided, overrides the style system prompt

    Returns:
        {"title": str, "story": str} or {"error": str}
    """
    if not settings.OPENROUTER_API_KEY:
        return {
            "error": "OpenRouter API key not configured. Set OPENROUTER_API_KEY in .env",
        }

    style_config = STORY_STYLES.get(style, STORY_STYLES["reddit_tifu"])
    system_prompt = custom_prompt or style_config["system"]

    user_message = "Write me a viral story."
    if topic:
        user_message = f"Write me a viral story about: {topic}"

    # Also ask for a title
    user_message += "\n\nReturn ONLY a JSON object with two fields: \"title\" (a catchy Reddit-style title) and \"story\" (the full story text). No markdown, no code blocks, just the raw JSON."

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://faceless-video-creator.app",
                    "X-Title": "Faceless Video Creator",
                },
                json={
                    "model": "meta-llama/llama-3.1-8b-instruct:free",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    "temperature": 0.9,
                    "max_tokens": 1024,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"].strip()

        # Try to parse as JSON
        import json

        # Clean up common issues: markdown code blocks, etc.
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        try:
            parsed = json.loads(content)
            return {
                "title": parsed.get("title", "Untitled Story"),
                "story": parsed.get("story", content),
            }
        except json.JSONDecodeError:
            # If JSON parsing fails, use the raw text
            # Try to split title from first line
            lines = content.split("\n", 1)
            title = lines[0].strip().strip("#").strip('"').strip()
            story = lines[1].strip() if len(lines) > 1 else content
            return {"title": title, "story": story}

    except httpx.HTTPStatusError as e:
        return {"error": f"OpenRouter API error: {e.response.status_code} - {e.response.text[:200]}"}
    except Exception as e:
        return {"error": f"Failed to generate story: {e}"}

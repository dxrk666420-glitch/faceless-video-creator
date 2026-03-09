"""Reddit story fetching service using PRAW."""

import praw

from app.config import settings


def get_reddit_client() -> praw.Reddit | None:
    """Create a Reddit client. Returns None if credentials aren't configured."""
    if not settings.REDDIT_CLIENT_ID or not settings.REDDIT_CLIENT_SECRET:
        return None
    return praw.Reddit(
        client_id=settings.REDDIT_CLIENT_ID,
        client_secret=settings.REDDIT_CLIENT_SECRET,
        user_agent=settings.REDDIT_USER_AGENT,
    )


def search_stories(
    subreddit: str = "AskReddit",
    sort: str = "hot",
    limit: int = 20,
    time_filter: str = "week",
) -> list[dict]:
    """Fetch stories from a subreddit.

    Returns list of story dicts with title, selftext, score, etc.
    """
    reddit = get_reddit_client()
    if reddit is None:
        return _get_sample_stories()

    sub = reddit.subreddit(subreddit)

    if sort == "hot":
        posts = sub.hot(limit=limit)
    elif sort == "top":
        posts = sub.top(time_filter=time_filter, limit=limit)
    elif sort == "new":
        posts = sub.new(limit=limit)
    else:
        posts = sub.hot(limit=limit)

    stories = []
    for post in posts:
        # Skip posts without text content
        if not post.selftext or post.selftext == "[removed]":
            continue
        stories.append({
            "id": post.id,
            "title": post.title,
            "selftext": post.selftext,
            "subreddit": str(post.subreddit),
            "score": post.score,
            "url": f"https://reddit.com{post.permalink}",
            "num_comments": post.num_comments,
            "author": str(post.author) if post.author else "[deleted]",
            "created_utc": post.created_utc,
        })

    return stories


def get_story_by_url(url: str) -> dict | None:
    """Fetch a specific Reddit story by URL."""
    reddit = get_reddit_client()
    if reddit is None:
        return None
    try:
        submission = reddit.submission(url=url)
        return {
            "id": submission.id,
            "title": submission.title,
            "selftext": submission.selftext,
            "subreddit": str(submission.subreddit),
            "score": submission.score,
            "url": url,
            "num_comments": submission.num_comments,
            "author": str(submission.author) if submission.author else "[deleted]",
            "created_utc": submission.created_utc,
        }
    except Exception:
        return None


# Popular story-focused subreddits
STORY_SUBREDDITS = [
    "AskReddit",
    "tifu",
    "AmItheAsshole",
    "relationship_advice",
    "TrueOffMyChest",
    "confession",
    "MaliciousCompliance",
    "pettyrevenge",
    "ProRevenge",
    "nosleep",
    "LetsNotMeet",
    "entitledparents",
    "AITAH",
]


def _get_sample_stories() -> list[dict]:
    """Return sample stories when Reddit API isn't configured."""
    return [
        {
            "id": "sample1",
            "title": "TIFU by accidentally sending my boss a meme instead of the quarterly report",
            "selftext": (
                "So this happened about two hours ago and I'm still dying inside. "
                "I was working late on the quarterly report, had about 15 tabs open. "
                "My friend sent me this absolutely hilarious meme about corporate life. "
                "I downloaded it to send to my group chat later. "
                "When I finished the report, I attached the file and hit send to my boss. "
                "Except I didn't attach the report. I attached the meme. "
                "The meme was literally making fun of bosses who send emails at midnight. "
                "My boss replied at 1 AM: 'This is actually funny but where's the report?' "
                "I wanted the earth to swallow me whole."
            ),
            "subreddit": "tifu",
            "score": 45200,
            "url": "https://reddit.com/r/tifu/sample1",
            "num_comments": 2341,
            "author": "corporate_disaster",
            "created_utc": 1709913600.0,
        },
        {
            "id": "sample2",
            "title": "What's the most unexplainable thing that's happened to you?",
            "selftext": (
                "I'll go first. When I was 12, I was walking home from school on a path I'd taken "
                "hundreds of times. Suddenly I noticed a small antique shop that I had never seen before. "
                "I went inside and the old man behind the counter looked at me and said 'You're early.' "
                "I asked what he meant and he just smiled. I bought a small compass for two dollars. "
                "The next day I tried to find the shop again. It wasn't there. "
                "The building was just an empty lot. I still have the compass. "
                "It doesn't point north. It always points to wherever I need to go."
            ),
            "subreddit": "AskReddit",
            "score": 38700,
            "url": "https://reddit.com/r/AskReddit/sample2",
            "num_comments": 5672,
            "author": "compass_holder",
            "created_utc": 1709827200.0,
        },
        {
            "id": "sample3",
            "title": "My neighbor has been leaving mysterious packages on my doorstep for 6 months",
            "selftext": (
                "This started in September last year. Every Tuesday morning, there's a small brown package "
                "on my doorstep. No return address, no postage, just my name written in neat handwriting. "
                "Inside is always something useful that I happen to need that exact week. "
                "Week one: batteries, right when my smoke detector started beeping. "
                "Week five: a specific brand of tea I mentioned liking in a phone call. "
                "Week twelve: an umbrella, the day before an unexpected rainstorm. "
                "I set up a camera. The packages appear between 3 and 4 AM. "
                "But the camera glitches every time. Just static for that one hour. "
                "Last Tuesday the package contained a note: 'Stop trying to find out. Just enjoy it.' "
                "I don't know what to do anymore."
            ),
            "subreddit": "nosleep",
            "score": 29400,
            "url": "https://reddit.com/r/nosleep/sample3",
            "num_comments": 1893,
            "author": "package_receiver",
            "created_utc": 1709740800.0,
        },
    ]

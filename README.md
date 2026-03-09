# Faceless Video Creator

Create viral faceless videos for TikTok, YouTube Shorts, and Instagram Reels — no face required.

## Features

### Reddit Story Videos
Turn viral Reddit stories into engaging narrated videos with captivating gameplay/satisfying backgrounds and word-by-word highlight captions (TikTok viral style).

### AI Video Generator (Sora)
Generate stunning videos from text descriptions using OpenAI's Sora API.

### Auto Video Clipper
Upload long-form videos and let AI find the best moments. Auto-clips to 9:16 vertical with captions.

### AI UGC Creator
Generate user-generated-content style videos for brands — customer testimonials, product reviews, and showcases.

## Tech Stack

- **Backend**: Python + FastAPI
- **Frontend**: Next.js 14 + Tailwind CSS
- **Database**: SQLite (via SQLAlchemy)
- **Video Processing**: MoviePy + FFmpeg
- **Text-to-Speech**: edge-tts (free, no API key) + ElevenLabs (optional)
- **Speech-to-Text**: OpenAI Whisper (local, free)
- **Reddit**: PRAW (Python Reddit API Wrapper)
- **Stock Footage**: Pexels API
- **AI Video**: OpenAI Sora API

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- FFmpeg installed (`apt install ffmpeg` or `brew install ffmpeg`)

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env     # Edit with your API keys
uvicorn app.main:app --reload
```

Backend runs at http://localhost:8000 (API docs at http://localhost:8000/docs)

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Frontend runs at http://localhost:3000

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | No | SQLite path (default: `sqlite:///./faceless.db`) |
| `PEXELS_API_KEY` | For backgrounds | Free at pexels.com/api |
| `REDDIT_CLIENT_ID` | For Reddit | Create app at reddit.com/prefs/apps |
| `REDDIT_CLIENT_SECRET` | For Reddit | Same as above |
| `OPENAI_API_KEY` | For Sora only | OpenAI API key |
| `ELEVENLABS_API_KEY` | No | Premium TTS (falls back to free edge-tts) |

**The app works without any API keys** using sample stories and free edge-tts voices. Add keys to unlock more features.

## Architecture

```
┌─────────────────┐     ┌──────────────────────────────────┐
│   Next.js UI    │────▶│         FastAPI Backend           │
│  (port 3000)    │     │         (port 8000)               │
└─────────────────┘     │                                    │
                        │  ┌─────────┐  ┌──────────────┐   │
                        │  │ Reddit  │  │  TTS Service  │   │
                        │  │ Service │  │  (edge-tts)   │   │
                        │  └─────────┘  └──────────────┘   │
                        │  ┌─────────┐  ┌──────────────┐   │
                        │  │ Pexels  │  │    Video      │   │
                        │  │ Service │  │  Compositor   │   │
                        │  └─────────┘  └──────────────┘   │
                        │  ┌─────────┐  ┌──────────────┐   │
                        │  │  Sora   │  │   Clipper     │   │
                        │  │ Service │  │   Service     │   │
                        │  └─────────┘  └──────────────┘   │
                        │  ┌─────────┐  ┌──────────────┐   │
                        │  │   UGC   │  │   Whisper     │   │
                        │  │ Service │  │  (Captions)   │   │
                        │  └─────────┘  └──────────────┘   │
                        │                                    │
                        │  SQLite DB  │  Media Files         │
                        └──────────────────────────────────┘
```

## License

MIT

# Blog Backend

FastAPI API for Ink & Co. — Google OAuth2, blogs, likes, comments, profiles.

## Docs

See [docs/TECHNICAL_DOCUMENTATION.md](docs/TECHNICAL_DOCUMENTATION.md) for architecture, API contracts, and usage.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs  
Redirect URI: `http://localhost:8000/api/auth/google/callback`

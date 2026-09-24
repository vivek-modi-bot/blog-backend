# Blog Backend

FastAPI backend for the blog site with Google OAuth2 and SQLite.

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

Redirect URI for Google OAuth: `http://localhost:8000/api/auth/google/callback`

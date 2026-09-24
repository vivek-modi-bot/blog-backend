import re
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..auth import create_access_token, create_oauth_state, get_current_user, verify_oauth_state
from ..config import settings
from ..database import get_db
from ..models import User
from ..schemas import UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


def _require_google_creds() -> None:
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=503,
            detail="Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in backend/.env",
        )


def _unique_username(db: Session, base: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "", base)[:40] or "user"
    candidate = cleaned
    n = 1
    while db.query(User).filter(User.username == candidate).first():
        candidate = f"{cleaned}{n}"
        n += 1
    return candidate


def _upsert_oauth_user(
    db: Session,
    *,
    provider: str,
    oauth_id: str,
    email: str,
    preferred_username: str,
) -> User:
    user = (
        db.query(User)
        .filter(User.oauth_provider == provider, User.oauth_id == oauth_id)
        .first()
    )
    if user:
        return user

    by_email = db.query(User).filter(User.email == email).first()
    if by_email:
        by_email.oauth_provider = provider
        by_email.oauth_id = oauth_id
        db.commit()
        db.refresh(by_email)
        return by_email

    user = User(
        username=_unique_username(db, preferred_username),
        email=email,
        oauth_provider=provider,
        oauth_id=oauth_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _frontend_token_redirect(token: str) -> RedirectResponse:
    return RedirectResponse(
        url=f"{settings.frontend_url}/auth/callback?token={token}",
        status_code=status.HTTP_302_FOUND,
    )


@router.get("/providers")
def list_providers():
    return {
        "google": bool(settings.google_client_id and settings.google_client_secret),
    }


@router.get("/google")
def google_login():
    _require_google_creds()
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": f"{settings.backend_url}/api/auth/google/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "prompt": "select_account",
        "state": create_oauth_state("google"),
    }
    return RedirectResponse(f"{GOOGLE_AUTH_URL}?{urlencode(params)}")


@router.get("/google/callback")
async def google_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    if error:
        raise HTTPException(status_code=400, detail=f"Google OAuth error: {error}")
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing OAuth code or state")

    verify_oauth_state(state, "google")
    _require_google_creds()

    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": f"{settings.backend_url}/api/auth/google/callback",
                "grant_type": "authorization_code",
            },
        )
        if token_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange Google code")
        access_token = token_res.json().get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="No Google access token returned")

        userinfo_res = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if userinfo_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch Google profile")
        info = userinfo_res.json()

    email = info.get("email")
    oauth_id = info.get("sub")
    if not email or not oauth_id:
        raise HTTPException(status_code=400, detail="Google account missing email")

    preferred = info.get("name") or email.split("@")[0]
    user = _upsert_oauth_user(
        db,
        provider="google",
        oauth_id=oauth_id,
        email=email,
        preferred_username=preferred,
    )
    app_token = create_access_token({"sub": user.username})
    return _frontend_token_redirect(app_token)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user

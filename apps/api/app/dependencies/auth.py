"""Firebase token verification dependency for FastAPI routes."""

from functools import lru_cache
from typing import Annotated

import firebase_admin
from firebase_admin import auth, credentials
from fastapi import Depends, HTTPException, Header
from app.config import settings


def _missing_firebase_env_keys() -> list[str]:
    missing: list[str] = []
    if not settings.firebase_project_id:
        missing.append("FIREBASE_PROJECT_ID")
    if not settings.firebase_client_email:
        missing.append("FIREBASE_CLIENT_EMAIL")
    if not settings.firebase_private_key:
        missing.append("FIREBASE_PRIVATE_KEY")
    return missing


@lru_cache(maxsize=1)
def _get_firebase_app() -> firebase_admin.App:
    """Initialise Firebase Admin SDK once (singleton)."""
    if firebase_admin._apps:
        return firebase_admin.get_app()

    missing = _missing_firebase_env_keys()
    if missing:
        raise RuntimeError(
            "Firebase Admin credentials are missing: " + ", ".join(missing)
        )

    private_key = settings.firebase_private_key.replace("\\n", "\n")
    cred = credentials.Certificate(
        {
            "type": "service_account",
            "project_id": settings.firebase_project_id,
            "client_email": settings.firebase_client_email,
            "private_key": private_key,
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    )
    return firebase_admin.initialize_app(cred)


def get_current_user(authorization: Annotated[str, Header()] = "") -> dict:
    """
    FastAPI dependency — validates the Firebase ID token in the
    `Authorization: Bearer <token>` header.

    Returns the decoded token dict with at least ``uid`` and ``email``.
    Raises HTTP 401 on missing, malformed, or expired tokens.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header.")

    try:
        _get_firebase_app()  # ensure initialised
    except RuntimeError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Firebase auth is not configured on API server: {exc}",
        )

    id_token = authorization.removeprefix("Bearer ").strip()
    try:
        decoded = auth.verify_id_token(id_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired Firebase token.")

    return decoded


CurrentUser = Annotated[dict, Depends(get_current_user)]

"""Firebase token verification dependency for FastAPI routes."""

import os
from functools import lru_cache
from typing import Annotated

import firebase_admin
from firebase_admin import auth, credentials
from fastapi import Depends, HTTPException, Header


@lru_cache(maxsize=1)
def _get_firebase_app() -> firebase_admin.App:
    """Initialise Firebase Admin SDK once (singleton)."""
    if firebase_admin._apps:
        return firebase_admin.get_app()

    private_key = os.environ["FIREBASE_PRIVATE_KEY"].replace("\\n", "\n")
    cred = credentials.Certificate(
        {
            "type": "service_account",
            "project_id": os.environ["FIREBASE_PROJECT_ID"],
            "client_email": os.environ["FIREBASE_CLIENT_EMAIL"],
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
    _get_firebase_app()  # ensure initialised

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header.")

    id_token = authorization.removeprefix("Bearer ").strip()
    try:
        decoded = auth.verify_id_token(id_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired Firebase token.")

    return decoded


CurrentUser = Annotated[dict, Depends(get_current_user)]

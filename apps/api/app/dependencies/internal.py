"""Internal service-to-service authentication dependencies."""

from typing import Annotated

from fastapi import Header, HTTPException

from app.config import settings


def verify_internal_request(
    x_internal_api_secret: Annotated[str | None, Header(alias="x-internal-api-secret")] = None,
) -> None:
    """Allow only trusted backend callers that know the shared secret."""
    if not x_internal_api_secret:
        raise HTTPException(status_code=401, detail="Missing internal API secret header.")

    if x_internal_api_secret != settings.internal_api_secret:
        raise HTTPException(status_code=403, detail="Invalid internal API secret.")

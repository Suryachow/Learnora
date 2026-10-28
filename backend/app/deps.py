"""Reusable FastAPI dependencies: database session, current user, admin gate."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .db import get_db
from .models import User
from .services.security import TokenError, decode_access_token

bearer_scheme = HTTPBearer(auto_error=False, description="JWT access token")

DbSession = Annotated[Session, Depends(get_db)]
Credentials = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]

_UNAUTHENTICATED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Please log in to continue.",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(db: DbSession, credentials: Credentials) -> User:
    if credentials is None or not credentials.credentials:
        raise _UNAUTHENTICATED

    try:
        user_id = decode_access_token(credentials.credentials)
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This account no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_optional_user(db: DbSession, credentials: Credentials) -> User | None:
    """For public pages that show extra detail once we know who is reading.

    A missing or unusable token is not an error here - the caller simply gets
    the anonymous view.
    """
    if credentials is None or not credentials.credentials:
        return None
    try:
        user_id = decode_access_token(credentials.credentials)
    except TokenError:
        return None
    return db.get(User, user_id)


OptionalUser = Annotated[User | None, Depends(get_optional_user)]


def get_current_admin(user: CurrentUser) -> User:
    """Admin gate enforced on the server for every admin route."""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You need administrator access to do that.",
        )
    return user


AdminUser = Annotated[User, Depends(get_current_admin)]


def require_active_subscription(user: CurrentUser) -> User:
    """402 is returned when a signed-in user has no active subscription."""
    if not user.has_active_subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="An active subscription is required to unlock tasks. Subscribe to continue.",
        )
    return user


SubscribedUser = Annotated[User, Depends(require_active_subscription)]

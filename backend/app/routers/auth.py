"""Registration and login."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ..deps import DbSession
from ..models import User
from ..schemas import ErrorResponse, LoginRequest, RegisterRequest, TokenResponse, UserPublic
from ..services.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

_INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="That email and password combination is not correct.",
    headers={"WWW-Authenticate": "Bearer"},
)


def _token_response(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.id),
        user=UserPublic.model_validate(user),
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an account and sign in",
    responses={409: {"model": ErrorResponse, "description": "Email already registered"}},
)
def register(payload: RegisterRequest, db: DbSession) -> TokenResponse:
    if db.scalar(select(User.id).where(User.email == payload.email)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists. Try logging in instead.",
        )

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        # Two concurrent registrations for the same email: the unique index wins.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists. Try logging in instead.",
        ) from exc

    db.refresh(user)
    return _token_response(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Sign in with email and password",
    responses={401: {"model": ErrorResponse, "description": "Wrong email or password"}},
)
def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise _INVALID_CREDENTIALS
    return _token_response(user)

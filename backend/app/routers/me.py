"""The signed-in user's own account: profile, security, preferences, billing."""

from fastapi import APIRouter, HTTPException, Query, status

from ..deps import CurrentUser, DbSession
from ..schemas import (
    BillingEntryOut,
    BillingOut,
    ErrorResponse,
    PasswordChangeRequest,
    PreferencesOut,
    PreferencesUpdateRequest,
    UserPublic,
    UserUpdateRequest,
)
from ..services import account as account_service
from ..services.account import AccountError

router = APIRouter(tags=["account"])


@router.get(
    "/me",
    response_model=UserPublic,
    summary="Get the signed-in user's profile",
    responses={401: {"model": ErrorResponse, "description": "Not authenticated"}},
)
def read_me(user: CurrentUser) -> UserPublic:
    return UserPublic.model_validate(user)


@router.patch(
    "/me",
    response_model=UserPublic,
    summary="Update the signed-in user's display name",
    responses={422: {"model": ErrorResponse, "description": "Invalid name"}},
)
def update_me(payload: UserUpdateRequest, db: DbSession, user: CurrentUser) -> UserPublic:
    if payload.name is not None:
        cleaned = payload.name.strip()
        if len(cleaned) < 2:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Please enter your full name (at least 2 characters).",
            )
        user.name = cleaned

    db.add(user)
    db.commit()
    db.refresh(user)
    return UserPublic.model_validate(user)


@router.post(
    "/me/password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change the password used to sign in",
    responses={400: {"model": ErrorResponse, "description": "Current password is wrong"}},
)
def change_password(
    payload: PasswordChangeRequest, db: DbSession, user: CurrentUser
) -> None:
    try:
        account_service.change_password(
            db,
            user,
            current_password=payload.current_password,
            new_password=payload.new_password,
        )
    except AccountError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get(
    "/me/preferences",
    response_model=PreferencesOut,
    summary="Notification and account preferences",
)
def read_preferences(user: CurrentUser) -> PreferencesOut:
    return PreferencesOut(**account_service.read_preferences(user))


@router.patch(
    "/me/preferences",
    response_model=PreferencesOut,
    summary="Update preferences (only the keys you send change)",
    responses={422: {"model": ErrorResponse, "description": "Unknown preference"}},
)
def update_preferences(
    payload: PreferencesUpdateRequest, db: DbSession, user: CurrentUser
) -> PreferencesOut:
    try:
        updated = account_service.update_preferences(db, user, payload.changes())
    except AccountError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return PreferencesOut(**updated)


@router.get(
    "/me/billing",
    response_model=BillingOut,
    summary="Subscription status and payment history",
)
def read_billing(
    db: DbSession,
    user: CurrentUser,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> BillingOut:
    items, total, total_paid = account_service.list_billing(
        db, user.id, limit=limit, offset=offset
    )
    return BillingOut(
        has_active_subscription=user.has_active_subscription,
        subscribed_until=user.subscribed_until,
        total_paid_paise=total_paid,
        payments=[
            BillingEntryOut(
                id=item.id,
                amount=item.amount,
                status=item.status.value,
                note=item.note,
                provider_ref=item.provider_ref,
                created_at=item.created_at,
            )
            for item in items
        ],
        total=total,
    )

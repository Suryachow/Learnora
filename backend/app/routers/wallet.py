"""The user's wallet: a balance computed from the ledger, plus history."""

from fastapi import APIRouter, Query

from ..deps import CurrentUser, DbSession
from ..models import TransactionKind
from ..schemas import Page, TransactionOut, WalletOut
from ..services import ledger
from ..services.settings_store import runtime_settings

router = APIRouter(tags=["wallet"])


@router.get(
    "/wallet",
    response_model=WalletOut,
    summary="Balance, pending rewards and recent transactions",
)
def read_wallet(
    db: DbSession,
    user: CurrentUser,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    kind: TransactionKind | None = Query(default=None, description="Filter the history"),
) -> WalletOut:
    items, total = ledger.list_transactions(
        db, user.id, limit=limit, offset=offset, kind=kind
    )
    live = runtime_settings(db)

    return WalletOut(
        balance_paise=ledger.wallet_balance(db, user.id),
        pending_paise=ledger.pending_balance(db, user.id),
        lifetime_earned_paise=ledger.lifetime_earned(db, user.id),
        withdrawn_paise=ledger.total_withdrawn(db, user.id),
        rewards_enabled=live.rewards_enabled,
        daily_limit_paise=live.reward_daily_limit_paise,
        transactions=Page[TransactionOut](
            items=[TransactionOut.model_validate(item) for item in items],
            total=total,
            limit=limit,
            offset=offset,
        ),
    )

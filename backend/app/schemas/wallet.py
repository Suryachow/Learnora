"""Wallet and ledger schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from ..models import TransactionKind, TransactionStatus
from .common import Page


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: TransactionKind
    amount: int
    status: TransactionStatus
    note: str
    task_id: int | None
    created_at: datetime


class WalletOut(BaseModel):
    """Balances are always derived from the ledger, never stored."""

    balance_paise: int
    pending_paise: int
    lifetime_earned_paise: int
    withdrawn_paise: int
    rewards_enabled: bool
    daily_limit_paise: int
    transactions: Page[TransactionOut]

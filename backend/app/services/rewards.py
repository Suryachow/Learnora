"""Reward granting - the only place a reward is added to a learner's wallet.

Rules, all enforced here and backed by a database constraint:
  * only a *passed* attempt, graded on the server, can pay out
  * a reward is paid at most once per (user, task)
  * finishing a lesson video pays at most once per (user, topic)
  * a single task never pays more than `reward_per_task_limit_paise`
  * a learner never earns more than `reward_daily_limit_paise` in one day
  * `rewards_enabled` is a global kill switch
"""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Task, Topic, Transaction, TransactionKind, TransactionStatus
from .ledger import add_transaction, rewards_paid_today
from .settings_store import RuntimeSettings

#: Why a reward was or was not paid. The API turns this into a sentence.
GRANTED = "granted"
ALREADY_REWARDED = "already_rewarded"
REWARDS_DISABLED = "rewards_disabled"
DAILY_LIMIT_REACHED = "daily_limit_reached"
NOTHING_TO_PAY = "nothing_to_pay"
LIMIT_CAPPED = "limit_capped"


@dataclass(frozen=True)
class RewardOutcome:
    granted: bool
    amount_paise: int
    reason: str
    #: What the task asked for, before the per-task/daily caps were applied.
    requested_paise: int = 0


def reward_already_granted(db: Session, user_id: int, task_id: int) -> bool:
    existing = db.scalar(
        select(Transaction.id).where(
            Transaction.user_id == user_id,
            Transaction.task_id == task_id,
            Transaction.kind == TransactionKind.reward,
        )
    )
    return existing is not None


def video_reward_already_granted(db: Session, user_id: int, topic_id: int) -> bool:
    existing = db.scalar(
        select(Transaction.id).where(
            Transaction.user_id == user_id,
            Transaction.topic_id == topic_id,
            Transaction.kind == TransactionKind.reward,
        )
    )
    return existing is not None


def grant_reward(
    db: Session,
    *,
    user_id: int,
    task: Task,
    settings: RuntimeSettings,
) -> RewardOutcome:
    """Append a reward row for a passed attempt, or explain why it was withheld.

    The caller owns the transaction: nothing is committed here, so the attempt
    record and this ledger row are written together or not at all.
    """
    requested = max(task.reward, 0)

    if reward_already_granted(db, user_id, task.id):
        return RewardOutcome(False, 0, ALREADY_REWARDED, requested)

    if not settings.rewards_enabled:
        return RewardOutcome(False, 0, REWARDS_DISABLED, requested)

    payable = min(requested, settings.reward_per_task_limit_paise)
    if payable <= 0:
        return RewardOutcome(False, 0, NOTHING_TO_PAY, requested)

    remaining_today = settings.reward_daily_limit_paise - rewards_paid_today(db, user_id)
    payable = min(payable, max(remaining_today, 0))
    if payable <= 0:
        return RewardOutcome(False, 0, DAILY_LIMIT_REACHED, requested)

    add_transaction(
        db,
        user_id=user_id,
        kind=TransactionKind.reward,
        amount=payable,
        status=TransactionStatus.completed,
        note=f"Reward: {task.title}",
        task_id=task.id,
    )
    reason = GRANTED if payable == requested else LIMIT_CAPPED
    return RewardOutcome(True, payable, reason, requested)


def grant_video_reward(
    db: Session,
    *,
    user_id: int,
    topic: Topic,
    settings: RuntimeSettings,
) -> RewardOutcome:
    """Append the lesson reward for a finished video, or explain why not.

    The same rules as a task reward, minus the per-task cap: once per topic,
    under the daily limit, behind the global kill switch. The caller owns the
    transaction, so the progress row and this ledger row land together.
    """
    requested = max(settings.video_reward_paise, 0)

    if video_reward_already_granted(db, user_id, topic.id):
        return RewardOutcome(False, 0, ALREADY_REWARDED, requested)

    if not settings.rewards_enabled:
        return RewardOutcome(False, 0, REWARDS_DISABLED, requested)

    if requested <= 0:
        return RewardOutcome(False, 0, NOTHING_TO_PAY, requested)

    remaining_today = settings.reward_daily_limit_paise - rewards_paid_today(db, user_id)
    payable = min(requested, max(remaining_today, 0))
    if payable <= 0:
        return RewardOutcome(False, 0, DAILY_LIMIT_REACHED, requested)

    add_transaction(
        db,
        user_id=user_id,
        kind=TransactionKind.reward,
        amount=payable,
        status=TransactionStatus.completed,
        note=f"Reward: {topic.title} (video)",
        topic_id=topic.id,
    )
    reason = GRANTED if payable == requested else LIMIT_CAPPED
    return RewardOutcome(True, payable, reason, requested)

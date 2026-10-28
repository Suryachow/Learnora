"""lesson reward: link a ledger row to the topic it was paid for

Revision ID: d5c1a7e94b20
Revises: c8d24b1f7a90
Create Date: 2026-10-25 09:10:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = 'd5c1a7e94b20'
down_revision: str | None = 'c8d24b1f7a90'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('transactions', sa.Column('topic_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_transactions_topic_id_topics',
        'transactions',
        'topics',
        ['topic_id'],
        ['id'],
        ondelete='SET NULL',
    )
    # One lesson reward per (user, topic). Task rewards keep topic_id NULL and
    # NULLs do not collide in a unique constraint, so they are unaffected.
    op.create_unique_constraint(
        'uq_transactions_user_topic_kind',
        'transactions',
        ['user_id', 'topic_id', 'kind'],
    )


def downgrade() -> None:
    op.drop_constraint('uq_transactions_user_topic_kind', 'transactions', type_='unique')
    op.drop_constraint('fk_transactions_topic_id_topics', 'transactions', type_='foreignkey')
    op.drop_column('transactions', 'topic_id')

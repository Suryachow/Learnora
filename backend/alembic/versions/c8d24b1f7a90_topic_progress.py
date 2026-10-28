"""topic progress: video completion and the understanding check

Revision ID: c8d24b1f7a90
Revises: b3f1c07ae2d4
Create Date: 2026-10-21 12:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = 'c8d24b1f7a90'
down_revision: str | None = 'b3f1c07ae2d4'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'topic_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('topic_id', sa.Integer(), nullable=False),
        sa.Column('video_completed_at', sa.DateTime(), nullable=True),
        sa.Column('video_watched_seconds', sa.Integer(), nullable=False),
        sa.Column('video_duration_seconds', sa.Integer(), nullable=False),
        sa.Column('understanding', sa.String(length=16), nullable=True),
        sa.Column('understanding_note', sa.Text(), nullable=False),
        sa.Column('understood_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            'video_watched_seconds >= 0 AND video_duration_seconds >= 0',
            name='ck_topic_progress_watch_times_non_negative',
        ),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'topic_id', name='uq_topic_progress_user_topic'),
    )
    op.create_index('ix_topic_progress_topic_id', 'topic_progress', ['topic_id'])
    op.create_index('ix_topic_progress_user_id', 'topic_progress', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_topic_progress_user_id', table_name='topic_progress')
    op.drop_index('ix_topic_progress_topic_id', table_name='topic_progress')
    op.drop_table('topic_progress')

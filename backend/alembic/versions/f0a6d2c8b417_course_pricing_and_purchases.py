"""course pricing and course purchases

Adds the amount an admin sets when creating a course (`price_paise`) together
with the extra catalogue detail (cover, level, duration, outcomes, access days),
and the `course_purchases` entitlement table plus the ledger link a purchase
writes.

Revision ID: f0a6d2c8b417
Revises: d5c1a7e94b20
Create Date: 2026-10-25 12:40:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = 'f0a6d2c8b417'
down_revision: str | None = 'd5c1a7e94b20'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- the course itself ------------------------------------------------
    op.add_column(
        'courses',
        sa.Column('price_paise', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column('courses', sa.Column('cover_image_url', sa.String(length=500), nullable=True))
    # Existing rows are drafts of the catalogue, so "beginner" is the safe default.
    op.add_column(
        'courses',
        sa.Column('level', sa.String(length=16), nullable=False, server_default='beginner'),
    )
    op.add_column('courses', sa.Column('duration_minutes', sa.Integer(), nullable=True))
    op.add_column(
        'courses',
        sa.Column('outcomes', sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
    )
    op.add_column('courses', sa.Column('access_days', sa.Integer(), nullable=True))

    op.create_check_constraint(
        'ck_courses_price_non_negative', 'courses', 'price_paise >= 0'
    )
    op.create_check_constraint(
        'ck_courses_duration_non_negative',
        'courses',
        'duration_minutes IS NULL OR duration_minutes >= 0',
    )
    op.create_check_constraint(
        'ck_courses_access_days_positive',
        'courses',
        'access_days IS NULL OR access_days >= 1',
    )

    # --- what a learner owns ----------------------------------------------
    op.create_table(
        'course_purchases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('amount_paise', sa.Integer(), nullable=False),
        sa.Column('purchased_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint('amount_paise >= 0', name='ck_course_purchases_amount_non_negative'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'course_id', name='uq_course_purchases_user_course'),
    )
    op.create_index('ix_course_purchases_user_id', 'course_purchases', ['user_id'])
    op.create_index('ix_course_purchases_course_id', 'course_purchases', ['course_id'])

    # --- the ledger row a purchase writes ---------------------------------
    op.add_column('transactions', sa.Column('course_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_transactions_course_id_courses',
        'transactions',
        'courses',
        ['course_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint('fk_transactions_course_id_courses', 'transactions', type_='foreignkey')
    op.drop_column('transactions', 'course_id')

    op.drop_index('ix_course_purchases_course_id', table_name='course_purchases')
    op.drop_index('ix_course_purchases_user_id', table_name='course_purchases')
    op.drop_table('course_purchases')

    op.drop_constraint('ck_courses_access_days_positive', 'courses', type_='check')
    op.drop_constraint('ck_courses_duration_non_negative', 'courses', type_='check')
    op.drop_constraint('ck_courses_price_non_negative', 'courses', type_='check')
    op.drop_column('courses', 'access_days')
    op.drop_column('courses', 'outcomes')
    op.drop_column('courses', 'duration_minutes')
    op.drop_column('courses', 'level')
    op.drop_column('courses', 'cover_image_url')
    op.drop_column('courses', 'price_paise')

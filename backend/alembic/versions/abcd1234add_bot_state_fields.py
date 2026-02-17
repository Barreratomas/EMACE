"""add bot state fields to vendor telegram integration

Revision ID: abcd1234addbottest
Revises: db3a11b0b611
Create Date: 2026-02-17 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "abcd1234addbottest"
down_revision: Union[str, None] = "db3a11b0b611"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "vendortelegramintegration",
        sa.Column("state", sa.String(length=32), nullable=False, server_default="active"),
    )
    op.add_column(
        "vendortelegramintegration",
        sa.Column("paused_at", sa.DateTime(timezone=False), nullable=True),
    )
    op.add_column(
        "vendortelegramintegration",
        sa.Column("deleted_at", sa.DateTime(timezone=False), nullable=True),
    )
    op.add_column(
        "vendortelegramintegration",
        sa.Column("paused_by_user_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_vendortelegramintegration_paused_by_user_id_user",
        "vendortelegramintegration",
        "user",
        ["paused_by_user_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_vendortelegramintegration_paused_by_user_id_user",
        "vendortelegramintegration",
        type_="foreignkey",
    )
    op.drop_column("vendortelegramintegration", "paused_by_user_id")
    op.drop_column("vendortelegramintegration", "deleted_at")
    op.drop_column("vendortelegramintegration", "paused_at")
    op.drop_column("vendortelegramintegration", "state")


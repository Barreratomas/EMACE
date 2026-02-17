"""add vendor mtproto session

Revision ID: 9c1a2d4f7a10
Revises: 5ef30cbd5f80
Create Date: 2026-02-16 21:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '9c1a2d4f7a10'
down_revision: Union[str, Sequence[str], None] = '5ef30cbd5f80'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'vendormtprotosession',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vendor_id', sa.Integer(), nullable=False),
        sa.Column('session_encrypted', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('phone_number', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('device_info', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('allowed_chats', sa.JSON(), nullable=False),
        sa.Column('last_error', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('last_heartbeat_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['vendor_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('vendor_id'),
    )


def downgrade() -> None:
    op.drop_table('vendormtprotosession')


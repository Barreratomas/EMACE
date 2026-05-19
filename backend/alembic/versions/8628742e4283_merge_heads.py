"""merge heads

Revision ID: 8628742e4283
Revises: abcd1234addbottest, dcdb615b8ed0
Create Date: 2026-05-19 15:50:46.038123

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '8628742e4283'
down_revision: Union[str, Sequence[str], None] = ('abcd1234addbottest', 'dcdb615b8ed0')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

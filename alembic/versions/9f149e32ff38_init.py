"""init

Revision ID: 9f149e32ff38
Revises: ab4f82758dfb
Create Date: 2026-07-22 10:00:09.580354

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f149e32ff38'
down_revision: Union[str, Sequence[str], None] = 'ab4f82758dfb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

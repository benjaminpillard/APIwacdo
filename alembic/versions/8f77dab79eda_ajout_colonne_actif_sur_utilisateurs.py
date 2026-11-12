"""ajout colonne actif sur utilisateurs

Revision ID: 8f77dab79eda
Revises: c1bd65457d10
Create Date: 2026-11-12 12:13:00.538675

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f77dab79eda'
down_revision: Union[str, Sequence[str], None] = 'c1bd65457d10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Les comptes existants sont actifs. sa.true() donne TRUE sous PostgreSQL et 1 sous SQLite
    # (PostgreSQL refuse l'entier 1 comme valeur par défaut d'un booléen).
    op.add_column(
        'utilisateurs',
        sa.Column('actif', sa.Boolean(), server_default=sa.true(), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # batch_alter_table : SQLite ne sait pas toujours supprimer une colonne directement
    with op.batch_alter_table('utilisateurs') as batch_op:
        batch_op.drop_column('actif')

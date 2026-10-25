"""Game disks: copy of another disk's version (source, progress, error)

Revision ID: 0018
Revises: 0017
Create Date: 2026-10-25 02:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0018'
down_revision: Union[str, Sequence[str], None] = '0017'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('game_disks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('copy_source', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('copy_percent', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('copy_error', sa.String(length=500), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('game_disks', schema=None) as batch_op:
        batch_op.drop_column('copy_error')
        batch_op.drop_column('copy_percent')
        batch_op.drop_column('copy_source')

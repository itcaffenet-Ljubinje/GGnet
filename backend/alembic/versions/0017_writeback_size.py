"""Machines: how much each PC wrote into its writebacks, and the size warning

Revision ID: 0017
Revises: 0016
Create Date: 2026-10-21 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0017'
down_revision: Union[str, Sequence[str], None] = '0016'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('machines', schema=None) as batch_op:
        batch_op.add_column(sa.Column('writeback_bytes', sa.BigInteger(), nullable=True))
        batch_op.add_column(sa.Column('writeback_large', sa.Boolean(), nullable=False,
                                      server_default=sa.false()))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('machines', schema=None) as batch_op:
        batch_op.drop_column('writeback_large')
        batch_op.drop_column('writeback_bytes')

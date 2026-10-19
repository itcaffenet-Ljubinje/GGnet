"""Boot Mode: the boot network card's PCI hardware ID, for Add hardware

Revision ID: 0014
Revises: 0013
Create Date: 2026-10-19 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0014'
down_revision: Union[str, Sequence[str], None] = '0013'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('machines', schema=None) as batch_op:
        batch_op.add_column(sa.Column('boot_nic', sa.String(length=64), nullable=True))
    with op.batch_alter_table('discovered_machines', schema=None) as batch_op:
        batch_op.add_column(sa.Column('boot_nic', sa.String(length=64), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('discovered_machines', schema=None) as batch_op:
        batch_op.drop_column('boot_nic')
    with op.batch_alter_table('machines', schema=None) as batch_op:
        batch_op.drop_column('boot_nic')

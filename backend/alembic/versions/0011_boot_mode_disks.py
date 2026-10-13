"""Boot Mode: OS images and per-machine OS writebacks

Revision ID: 0011
Revises: 0010
Create Date: 2026-10-13 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0011'
down_revision: Union[str, Sequence[str], None] = '0010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('game_disks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('kind', sa.Enum('game', 'os', name='diskkind',
                                                      native_enum=False, length=16),
                                      nullable=False, server_default='game'))
    with op.batch_alter_table('machines', schema=None) as batch_op:
        batch_op.add_column(sa.Column('os_disk_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('os_clone_zvol', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('os_clone_snapshot', sa.String(length=320), nullable=True))
        batch_op.create_index(batch_op.f('ix_machines_os_disk_id'), ['os_disk_id'], unique=False)
        batch_op.create_foreign_key(batch_op.f('fk_machines_os_disk_id_game_disks'), 'game_disks',
                                    ['os_disk_id'], ['id'], ondelete='RESTRICT')


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('machines', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('fk_machines_os_disk_id_game_disks'), type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_machines_os_disk_id'))
        batch_op.drop_column('os_clone_snapshot')
        batch_op.drop_column('os_clone_zvol')
        batch_op.drop_column('os_disk_id')
    with op.batch_alter_table('game_disks', schema=None) as batch_op:
        batch_op.drop_column('kind')

"""Discovery: PCs that knocked (iPXE or agent) but are not registered

Revision ID: 0012
Revises: 0011
Create Date: 2026-10-14 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0012'
down_revision: Union[str, Sequence[str], None] = '0011'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'discovered_machines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('mac', sa.String(length=17), nullable=False),
        sa.Column('source', sa.Enum('pxe', 'agent', name='discoverysource',
                                    native_enum=False, length=16), nullable=False),
        sa.Column('hostname', sa.String(length=64), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('agent_version', sa.String(length=32), nullable=True),
        sa.Column('seen_count', sa.Integer(), nullable=False),
        sa.Column('ignored', sa.Boolean(), nullable=False),
        sa.Column('first_seen_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_discovered_machines')),
        sa.UniqueConstraint('mac', name=op.f('uq_discovered_machines_mac')),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('discovered_machines')

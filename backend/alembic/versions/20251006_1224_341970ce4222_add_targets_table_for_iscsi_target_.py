"""Add targets table for iSCSI target management

Revision ID: 341970ce4222
Revises: 
Create Date: 2025-10-06 12:24:09.112907

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '341970ce4222'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop existing targets table if it exists
    op.drop_table('targets')
    
    # Create new targets table
    op.create_table('targets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('target_id', sa.String(length=100), nullable=False),
        sa.Column('iqn', sa.String(length=255), nullable=False),
        sa.Column('machine_id', sa.Integer(), nullable=False),
        sa.Column('image_id', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('image_path', sa.String(length=500), nullable=False),
        sa.Column('initiator_iqn', sa.String(length=255), nullable=False),
        sa.Column('lun_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'ERROR', 'PENDING', name='targetstatus'), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['image_id'], ['images.id'], ),
        sa.ForeignKeyConstraint(['machine_id'], ['machines.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_targets_id'), 'targets', ['id'], unique=False)
    op.create_index(op.f('ix_targets_target_id'), 'targets', ['target_id'], unique=True)
    op.create_index(op.f('ix_targets_iqn'), 'targets', ['iqn'], unique=True)


def downgrade() -> None:
    # Drop the new targets table
    op.drop_index(op.f('ix_targets_iqn'), table_name='targets')
    op.drop_index(op.f('ix_targets_target_id'), table_name='targets')
    op.drop_index(op.f('ix_targets_id'), table_name='targets')
    op.drop_table('targets')
    
    # Recreate old targets table structure (simplified)
    op.create_table('targets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('iqn', sa.String(length=500), nullable=False),
        sa.Column('portal_ip', sa.String(length=15), nullable=False),
        sa.Column('portal_port', sa.Integer(), nullable=False),
        sa.Column('target_type', sa.String(length=11), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('machine_id', sa.Integer(), nullable=False),
        sa.Column('system_image_id', sa.Integer(), nullable=False),
        sa.Column('extra_disk_image_id', sa.Integer(), nullable=True),
        sa.Column('extra_disk_mountpoint', sa.String(length=10), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_connected', sa.DateTime(), nullable=True),
        sa.Column('connection_count', sa.Integer(), nullable=False),
        sa.Column('max_connections', sa.Integer(), nullable=False),
        sa.Column('authentication_required', sa.Boolean(), nullable=False),
        sa.Column('chap_username', sa.String(length=100), nullable=True),
        sa.Column('chap_password', sa.String(length=100), nullable=True),
        sa.Column('read_only', sa.Boolean(), nullable=False),
        sa.Column('block_size', sa.Integer(), nullable=False),
        sa.Column('cache_enabled', sa.Boolean(), nullable=False),
        sa.Column('max_retries', sa.Integer(), nullable=False),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['extra_disk_image_id'], ['images.id'], ),
        sa.ForeignKeyConstraint(['machine_id'], ['machines.id'], ),
        sa.ForeignKeyConstraint(['system_image_id'], ['images.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_targets_name', 'targets', ['name'], unique=False)

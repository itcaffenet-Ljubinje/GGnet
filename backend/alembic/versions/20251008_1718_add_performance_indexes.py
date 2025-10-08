"""Add performance indexes

Revision ID: perf_indexes_001
Revises: 9d9e5558e847
Create Date: 2025-10-08 17:18:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'perf_indexes_001'
down_revision = '9d9e5558e847'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add indexes for better query performance"""
    
    # Session model indexes
    op.create_index(
        'ix_sessions_status',
        'sessions',
        ['status'],
        unique=False
    )
    op.create_index(
        'ix_sessions_machine_id',
        'sessions',
        ['machine_id'],
        unique=False
    )
    op.create_index(
        'ix_sessions_target_id',
        'sessions',
        ['target_id'],
        unique=False
    )
    op.create_index(
        'ix_sessions_started_at',
        'sessions',
        ['started_at'],
        unique=False
    )
    op.create_index(
        'ix_sessions_last_activity',
        'sessions',
        ['last_activity'],
        unique=False
    )
    
    # Image model indexes
    op.create_index(
        'ix_images_status',
        'images',
        ['status'],
        unique=False
    )
    op.create_index(
        'ix_images_image_type',
        'images',
        ['image_type'],
        unique=False
    )
    op.create_index(
        'ix_images_created_at',
        'images',
        ['created_at'],
        unique=False
    )
    
    # Machine model indexes
    op.create_index(
        'ix_machines_status',
        'machines',
        ['status'],
        unique=False
    )
    op.create_index(
        'ix_machines_is_online',
        'machines',
        ['is_online'],
        unique=False
    )
    op.create_index(
        'ix_machines_last_seen',
        'machines',
        ['last_seen'],
        unique=False
    )


def downgrade() -> None:
    """Remove performance indexes"""
    
    # Drop session indexes
    op.drop_index('ix_sessions_last_activity', table_name='sessions')
    op.drop_index('ix_sessions_started_at', table_name='sessions')
    op.drop_index('ix_sessions_target_id', table_name='sessions')
    op.drop_index('ix_sessions_machine_id', table_name='sessions')
    op.drop_index('ix_sessions_status', table_name='sessions')
    
    # Drop image indexes
    op.drop_index('ix_images_created_at', table_name='images')
    op.drop_index('ix_images_image_type', table_name='images')
    op.drop_index('ix_images_status', table_name='images')
    
    # Drop machine indexes
    op.drop_index('ix_machines_last_seen', table_name='machines')
    op.drop_index('ix_machines_is_online', table_name='machines')
    op.drop_index('ix_machines_status', table_name='machines')

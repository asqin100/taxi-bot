"""Add last_export_at to users table

Revision ID: add_last_export
Revises: add_ban_system
Create Date: 2026-03-19 17:33:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_last_export'
down_revision = 'add_ban_system'
branch_labels = None
depends_on = None


def upgrade():
    # Add last_export_at column to users table
    op.add_column('users', sa.Column('last_export_at', sa.DateTime(), nullable=True))


def downgrade():
    # Remove last_export_at column
    op.drop_column('users', 'last_export_at')

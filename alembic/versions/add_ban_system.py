"""Add ban system fields to users table

Revision ID: add_ban_system
Revises: add_where_to_go_limit
Create Date: 2026-03-19 17:32:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_ban_system'
down_revision = 'add_where_to_go_limit'
branch_labels = None
depends_on = None


def upgrade():
    # Add ban system columns to users table
    op.add_column('users', sa.Column('is_banned', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('ban_reason', sa.String(length=256), nullable=True))
    op.add_column('users', sa.Column('banned_at', sa.DateTime(), nullable=True))


def downgrade():
    # Remove ban system columns
    op.drop_column('users', 'banned_at')
    op.drop_column('users', 'ban_reason')
    op.drop_column('users', 'is_banned')

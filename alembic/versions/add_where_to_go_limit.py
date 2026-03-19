"""Add where to go daily limit tracking

Revision ID: add_where_to_go_limit
Revises: add_preferred_tariff
Create Date: 2026-03-19 17:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_where_to_go_limit'
down_revision = 'add_preferred_tariff'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns for where to go daily limit tracking
    op.add_column('users', sa.Column('where_to_go_requests_today', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('where_to_go_reset_date', sa.DateTime(), nullable=True))


def downgrade():
    # Remove columns
    op.drop_column('users', 'where_to_go_reset_date')
    op.drop_column('users', 'where_to_go_requests_today')

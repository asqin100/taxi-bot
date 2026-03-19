"""Add geo alerts daily limit tracking

Revision ID: add_geo_alerts_limit
Revises:
Create Date: 2026-03-07

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_geo_alerts_limit'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns for geo alerts daily limit tracking
    op.add_column('users', sa.Column('geo_alerts_sent_today', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('geo_alerts_reset_date', sa.DateTime(), nullable=True))


def downgrade():
    # Remove columns
    op.drop_column('users', 'geo_alerts_reset_date')
    op.drop_column('users', 'geo_alerts_sent_today')

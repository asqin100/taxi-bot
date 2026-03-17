"""Add venue info to events table

Revision ID: add_venue_info
Revises: add_geo_alerts_limit
Create Date: 2026-03-17 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_venue_info'
down_revision = 'add_geo_alerts_limit'
branch_labels = None
depends_on = None


def upgrade():
    # Add venue information columns to events table
    op.add_column('events', sa.Column('venue_name', sa.String(length=256), nullable=True))
    op.add_column('events', sa.Column('venue_lat', sa.Float(), nullable=True))
    op.add_column('events', sa.Column('venue_lon', sa.Float(), nullable=True))


def downgrade():
    # Remove venue information columns
    op.drop_column('events', 'venue_lon')
    op.drop_column('events', 'venue_lat')
    op.drop_column('events', 'venue_name')

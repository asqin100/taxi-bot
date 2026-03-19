"""Add preferred_tariff to users table

Revision ID: add_preferred_tariff
Revises: add_venue_info
Create Date: 2026-03-19 06:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_preferred_tariff'
down_revision = 'add_venue_info'
branch_labels = None
depends_on = None


def upgrade():
    # Add preferred_tariff column to users table
    op.add_column('users', sa.Column('preferred_tariff', sa.String(length=20), nullable=False, server_default='econom'))


def downgrade():
    # Remove preferred_tariff column
    op.drop_column('users', 'preferred_tariff')

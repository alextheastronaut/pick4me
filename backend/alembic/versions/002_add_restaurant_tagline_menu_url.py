"""add tagline and menu_url to restaurants

Revision ID: 002
Revises: 001
Create Date: 2026-05-25

"""
import sqlalchemy as sa
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("restaurants", sa.Column("tagline", sa.Text(), nullable=True))
    op.add_column("restaurants", sa.Column("menu_url", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("restaurants", "menu_url")
    op.drop_column("restaurants", "tagline")

"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-05-25

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    op.create_table(
        "restaurants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("slug", sa.Text, unique=True, nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "menu_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("restaurant_id", UUID(as_uuid=True), sa.ForeignKey("restaurants.id"), nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("price_cents", sa.Integer, nullable=False),
        sa.Column("image_s3_key", sa.Text),
        sa.Column("is_available", sa.Boolean, server_default="true"),
        sa.Column("is_signature", sa.Boolean, server_default="false"),
        sa.Column("popularity_score", sa.Float, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "tags",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("key", sa.Text, unique=True, nullable=False),
        sa.Column("category", sa.Text, nullable=False),
        sa.Column("display_name", sa.Text, nullable=False),
    )

    op.create_table(
        "menu_item_tags",
        sa.Column("menu_item_id", UUID(as_uuid=True), sa.ForeignKey("menu_items.id"), primary_key=True),
        sa.Column("tag_id", UUID(as_uuid=True), sa.ForeignKey("tags.id"), primary_key=True),
        sa.Column("weight", sa.Float, server_default="1.0"),
    )

    op.create_table(
        "quiz_questions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("restaurant_id", UUID(as_uuid=True), sa.ForeignKey("restaurants.id"), nullable=True),
        sa.Column("key", sa.Text, nullable=False),
        sa.Column("prompt", sa.Text, nullable=False),
        sa.Column("order_index", sa.Integer, nullable=False),
    )

    op.create_table(
        "quiz_answers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("question_id", UUID(as_uuid=True), sa.ForeignKey("quiz_questions.id"), nullable=False),
        sa.Column("key", sa.Text, nullable=False),
        sa.Column("label", sa.Text, nullable=False),
        sa.Column("order_index", sa.Integer, nullable=False),
    )

    op.create_table(
        "recommendation_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("restaurant_id", UUID(as_uuid=True), sa.ForeignKey("restaurants.id"), nullable=False),
        sa.Column("session_id", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("quiz_answers", JSONB, nullable=False),
        sa.Column("recommended_item_ids", JSONB, nullable=False),
        sa.Column("scores", JSONB, nullable=False),
        sa.Column("client_meta", JSONB),
    )

    op.create_index(
        "ix_menu_items_restaurant_available",
        "menu_items",
        ["restaurant_id"],
        postgresql_where=sa.text("is_available"),
    )
    op.create_index("ix_menu_item_tags_tag_id", "menu_item_tags", ["tag_id"])
    op.create_index(
        "ix_recommendation_events_restaurant_created",
        "recommendation_events",
        ["restaurant_id", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    op.drop_index("ix_recommendation_events_restaurant_created", table_name="recommendation_events")
    op.drop_index("ix_menu_item_tags_tag_id", table_name="menu_item_tags")
    op.drop_index("ix_menu_items_restaurant_available", table_name="menu_items")
    op.drop_table("recommendation_events")
    op.drop_table("quiz_answers")
    op.drop_table("quiz_questions")
    op.drop_table("menu_item_tags")
    op.drop_table("tags")
    op.drop_table("menu_items")
    op.drop_table("restaurants")

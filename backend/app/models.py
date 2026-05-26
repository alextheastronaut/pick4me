import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Restaurant(Base):
    __tablename__ = "restaurants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    tagline: Mapped[str | None] = mapped_column(Text)
    menu_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    menu_items: Mapped[list["MenuItem"]] = relationship(back_populates="restaurant")
    quiz_questions: Mapped[list["QuizQuestion"]] = relationship(back_populates="restaurant")
    recommendation_events: Mapped[list["RecommendationEvent"]] = relationship(back_populates="restaurant")


class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("restaurants.id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    image_s3_key: Mapped[str | None] = mapped_column(Text)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    is_signature: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    popularity_score: Mapped[float] = mapped_column(Float, default=0.0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    restaurant: Mapped["Restaurant"] = relationship(back_populates="menu_items")
    item_tags: Mapped[list["MenuItemTag"]] = relationship(back_populates="menu_item", cascade="all, delete-orphan")


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)

    item_tags: Mapped[list["MenuItemTag"]] = relationship(back_populates="tag")


class MenuItemTag(Base):
    __tablename__ = "menu_item_tags"
    __table_args__ = (UniqueConstraint("menu_item_id", "tag_id"),)

    menu_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("menu_items.id"), primary_key=True
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tags.id"), primary_key=True
    )
    weight: Mapped[float] = mapped_column(Float, default=1.0, server_default="1.0")

    menu_item: Mapped["MenuItem"] = relationship(back_populates="item_tags")
    tag: Mapped["Tag"] = relationship(back_populates="item_tags")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("restaurants.id"), nullable=True)
    key: Mapped[str] = mapped_column(Text, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)

    restaurant: Mapped["Restaurant | None"] = relationship(back_populates="quiz_questions")
    answers: Mapped[list["QuizAnswer"]] = relationship(back_populates="question", order_by="QuizAnswer.order_index")


class QuizAnswer(Base):
    __tablename__ = "quiz_answers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quiz_questions.id"), nullable=False)
    key: Mapped[str] = mapped_column(Text, nullable=False)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)

    question: Mapped["QuizQuestion"] = relationship(back_populates="answers")


class RecommendationEvent(Base):
    __tablename__ = "recommendation_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("restaurants.id"), nullable=False)
    session_id: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    quiz_answers: Mapped[dict] = mapped_column(JSONB, nullable=False)
    recommended_item_ids: Mapped[list] = mapped_column(JSONB, nullable=False)
    scores: Mapped[dict] = mapped_column(JSONB, nullable=False)
    client_meta: Mapped[dict | None] = mapped_column(JSONB)

    restaurant: Mapped["Restaurant"] = relationship(back_populates="recommendation_events")

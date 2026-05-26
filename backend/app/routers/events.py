import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import RecommendationEvent, Restaurant

router = APIRouter()

ALLOWED_EVENT_TYPES = frozenset({
    "view_screen",
    "quiz_answer",
    "quiz_checkpoint_choice",
    "recommendation_shown",
    "menu_clickthrough",
    "next_best_clicked",
    "retry_clicked",
    "feedback_submitted",
    "language_changed",
    "quiz_started",
    "quiz_abandoned",
    "session_end",
})


class EventRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=128)
    event_type: str
    payload: dict[str, Any]
    client_ts: str
    language: str | None = Field(default=None, min_length=2, max_length=8)

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        if v not in ALLOWED_EVENT_TYPES:
            raise ValueError(f"Unknown event_type '{v}'. Must be one of: {', '.join(sorted(ALLOWED_EVENT_TYPES))}")
        return v

    @field_validator("client_ts")
    @classmethod
    def validate_client_ts(cls, v: str) -> str:
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("client_ts must be a parseable ISO 8601 datetime string")
        return v

    @model_validator(mode="after")
    def validate_payload_size(self) -> "EventRequest":
        if len(json.dumps(self.payload).encode()) > 16 * 1024:
            raise ValueError("payload serialized JSON exceeds 16 KB limit")
        return self


@router.post("/restaurants/{slug}/events", status_code=204)
async def track_event(
    slug: str,
    body: EventRequest,
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(select(Restaurant).where(Restaurant.slug == slug))
    restaurant = result.scalar_one_or_none()
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # For recommendation_shown, index the key fields directly for cheap analytics.
    # All other events use empty sentinels because the columns are NOT NULL in the schema.
    if body.event_type == "recommendation_shown":
        quiz_answers = body.payload.get("answers") or {}
        recommended_item_ids = body.payload.get("ranked_ids") or []
        scores = body.payload.get("scores") or {}
    else:
        quiz_answers = {}
        recommended_item_ids = []
        scores = {}

    event = RecommendationEvent(
        restaurant_id=restaurant.id,
        session_id=body.session_id,
        quiz_answers=quiz_answers,
        recommended_item_ids=recommended_item_ids,
        scores=scores,
        client_meta={
            "event_type": body.event_type,
            "client_ts": body.client_ts,
            "language": body.language,
            "payload": body.payload,
        },
    )
    db.add(event)
    await db.commit()

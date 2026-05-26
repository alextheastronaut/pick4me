import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal, get_db
from app.models import MenuItem, MenuItemTag, RecommendationEvent, Restaurant, Tag
from app.recommender import ScoredItem, build_items_with_tags, recommend

router = APIRouter()


class RecommendationRequest(BaseModel):
    quiz_answers: dict[str, str]
    session_id: str


class MenuItemOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    price_cents: int
    is_signature: bool
    popularity_score: float

    model_config = {"from_attributes": True}


class RecommendationItem(BaseModel):
    item: MenuItemOut
    score: float
    reasons: list[str]


class RecommendationResponse(BaseModel):
    recommendations: list[RecommendationItem]


async def _write_event(
    restaurant_id: uuid.UUID,
    session_id: str,
    quiz_answers: dict[str, str],
    scored: list[ScoredItem],
) -> None:
    async with AsyncSessionLocal() as db:
        event = RecommendationEvent(
            restaurant_id=restaurant_id,
            session_id=session_id,
            quiz_answers=quiz_answers,
            recommended_item_ids=[str(s.item.id) for s in scored],
            scores={str(s.item.id): s.score for s in scored},
        )
        db.add(event)
        await db.commit()


@router.post("/restaurants/{slug}/recommendations", response_model=RecommendationResponse)
async def get_recommendations(
    slug: str,
    body: RecommendationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> Any:
    result = await db.execute(select(Restaurant).where(Restaurant.slug == slug))
    restaurant = result.scalar_one_or_none()
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    items_result = await db.execute(
        select(MenuItem)
        .where(MenuItem.restaurant_id == restaurant.id, MenuItem.is_available.is_(True))
        .options(selectinload(MenuItem.item_tags).selectinload(MenuItemTag.tag))
    )
    menu_items = list(items_result.scalars().all())

    items_with_tags = build_items_with_tags(menu_items)
    scored = recommend(items_with_tags, body.quiz_answers)

    background_tasks.add_task(
        _write_event, restaurant.id, body.session_id, body.quiz_answers, scored
    )

    return RecommendationResponse(
        recommendations=[
            RecommendationItem(
                item=MenuItemOut.model_validate(s.item),
                score=round(s.score, 4),
                reasons=s.reasons,
            )
            for s in scored
        ]
    )

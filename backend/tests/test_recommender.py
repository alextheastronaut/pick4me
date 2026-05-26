"""
Tests require a running Postgres instance at the DATABASE_URL env var
(pytest-env sets this to pick4me_test — see pyproject.toml).

Create the test DB once before running:
  psql -U pick4me -c "CREATE DATABASE pick4me_test;"
"""
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.database import Base
from app.main import app
from app.models import MenuItem, MenuItemTag, RecommendationEvent, Restaurant, Tag
from app.recommender import ItemWithTags, TagInfo, recommend
from app.settings import settings


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    """Create all tables once for the session using the sync engine, then drop them."""
    sync_engine = create_engine(settings.database_sync_url)
    Base.metadata.drop_all(sync_engine)
    Base.metadata.create_all(sync_engine)
    yield
    Base.metadata.drop_all(sync_engine)
    sync_engine.dispose()


@pytest_asyncio.fixture
async def db():
    # NullPool: each call creates a fresh connection, avoiding event-loop-per-test issues.
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()
    await engine.dispose()


def _make_test_session():
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def restaurant(db: AsyncSession) -> Restaurant:
    r = Restaurant(id=uuid.uuid4(), slug=f"test-{uuid.uuid4().hex[:8]}", name="Test Place")
    db.add(r)
    await db.commit()
    await db.refresh(r)
    return r


# ---------------------------------------------------------------------------
# Test 1 — hard filter excludes items with an excluded tag
# ---------------------------------------------------------------------------

async def test_hard_filter_excludes_dairy_for_vegan(db: AsyncSession, restaurant: Restaurant):
    dairy_item = MenuItem(
        id=uuid.uuid4(), restaurant_id=restaurant.id,
        name="Cream Soup", price_cents=1200, popularity_score=5.0,
    )
    safe_item = MenuItem(
        id=uuid.uuid4(), restaurant_id=restaurant.id,
        name="Fruit Salad", price_cents=900, popularity_score=5.0,
    )
    db.add_all([dairy_item, safe_item])
    await db.commit()

    # Use canonical tag keys so ANSWER_EFFECTS mapping applies correctly
    items_with_tags = [
        ItemWithTags(
            item=dairy_item,
            tags=[TagInfo(key="contains_dairy", display_name="Contains Dairy", weight=1.0)],
        ),
        ItemWithTags(
            item=safe_item,
            tags=[TagInfo(key="vegan", display_name="Vegan", weight=1.0)],
        ),
    ]

    results = recommend(items_with_tags, {"diet": "vegan"})

    result_ids = {r.item.id for r in results}
    assert dairy_item.id not in result_ids, "Dairy item must be excluded for vegan diet"
    assert safe_item.id in result_ids, "Vegan item must appear in results"


# ---------------------------------------------------------------------------
# Test 2 — scoring picks the highest-weighted item
# ---------------------------------------------------------------------------

async def test_scoring_picks_highest_weighted_item(restaurant: Restaurant):
    low = MenuItem(id=uuid.uuid4(), restaurant_id=restaurant.id, name="Low", price_cents=1000, popularity_score=0.0)
    mid = MenuItem(id=uuid.uuid4(), restaurant_id=restaurant.id, name="Mid", price_cents=1000, popularity_score=0.0)
    high = MenuItem(id=uuid.uuid4(), restaurant_id=restaurant.id, name="High", price_cents=1000, popularity_score=0.0)

    items_with_tags = [
        ItemWithTags(item=low, tags=[TagInfo(key="spicy", display_name="Spicy", weight=0.5)]),
        ItemWithTags(item=mid, tags=[TagInfo(key="spicy", display_name="Spicy", weight=1.0)]),
        ItemWithTags(item=high, tags=[TagInfo(key="spicy", display_name="Spicy", weight=2.0)]),
    ]

    results = recommend(items_with_tags, {"flavor": "spicy"})

    assert len(results) == 3
    assert results[0].item.id == high.id, "Highest-weight item must rank first"
    assert results[1].item.id == mid.id
    assert results[2].item.id == low.id


# ---------------------------------------------------------------------------
# Test 3 — event row is written after POST to endpoint
# ---------------------------------------------------------------------------

async def test_event_written_after_recommendation(db: AsyncSession, restaurant: Restaurant):
    # Create an item — no special tags needed; we use no_restrictions answers
    item = MenuItem(
        id=uuid.uuid4(), restaurant_id=restaurant.id,
        name="Plain Dish", price_cents=1500, popularity_score=6.0,
    )
    db.add(item)
    await db.commit()

    session_id = f"sess-{uuid.uuid4().hex}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            f"/api/v1/restaurants/{restaurant.slug}/recommendations",
            json={"quiz_answers": {"diet": "no_restrictions"}, "session_id": session_id},
        )

    assert response.status_code == 200

    # Open a fresh session to avoid stale transaction snapshot
    async with _make_test_session()() as verify_db:
        result = await verify_db.execute(
            select(RecommendationEvent).where(
                RecommendationEvent.restaurant_id == restaurant.id,
                RecommendationEvent.session_id == session_id,
            )
        )
        event = result.scalar_one_or_none()

    assert event is not None, "RecommendationEvent must be written to the DB"
    assert event.session_id == session_id
    assert event.restaurant_id == restaurant.id

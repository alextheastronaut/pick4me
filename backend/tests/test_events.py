"""
Tests for POST /api/v1/restaurants/{slug}/events.
Requires a running Postgres instance — same setup as test_recommender.py.

All HTTP tests are in a single async function so they share one event loop,
avoiding asyncpg pool-invalidation between separate test invocations.
"""
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.database import Base
from app.main import app
from app.models import RecommendationEvent, Restaurant
from app.settings import settings

ALL_EVENT_TYPES = [
    "view_screen",
    "quiz_answer",
    "quiz_checkpoint_choice",
    "recommendation_shown",
    "menu_clickthrough",
    "retry_clicked",
    "feedback_submitted",
    "language_changed",
    "quiz_started",
    "quiz_abandoned",
]


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    sync_engine = create_engine(settings.database_sync_url)
    Base.metadata.drop_all(sync_engine)
    Base.metadata.create_all(sync_engine)
    yield
    Base.metadata.drop_all(sync_engine)
    sync_engine.dispose()


async def test_events_endpoint():
    """All endpoint behaviours in one function to share a single event loop."""
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    # Seed a restaurant for this test run
    slug = f"test-{uuid.uuid4().hex[:8]}"
    async with session_factory() as session:
        restaurant = Restaurant(id=uuid.uuid4(), slug=slug, name="Test Place")
        session.add(restaurant)
        await session.commit()
        await session.refresh(restaurant)

    valid_body = {
        "session_id": "test-session",
        "event_type": "view_screen",
        "payload": {"screen": "landing"},
        "client_ts": "2026-05-26T12:00:00.000Z",
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:

        # ── Happy path: all event_types return 204 and write a row ──────────
        for event_type in ALL_EVENT_TYPES:
            session_id = f"sess-{uuid.uuid4().hex}"
            r = await client.post(
                f"/api/v1/restaurants/{slug}/events",
                json={
                    "session_id": session_id,
                    "event_type": event_type,
                    "payload": {"screen": "landing"},
                    "client_ts": "2026-05-26T12:00:00.000Z",
                },
            )
            assert r.status_code == 204, f"event_type={event_type} got {r.status_code}"
            assert r.content == b"", f"event_type={event_type} returned body"

            async with session_factory() as verify_db:
                from sqlalchemy import select
                result = await verify_db.execute(
                    select(RecommendationEvent).where(RecommendationEvent.session_id == session_id)
                )
                event = result.scalar_one_or_none()
            assert event is not None, f"No row written for event_type={event_type}"
            assert event.client_meta["event_type"] == event_type

        # ── 404 on unknown slug ─────────────────────────────────────────────
        r = await client.post(
            "/api/v1/restaurants/no-such-place/events",
            json=valid_body,
        )
        assert r.status_code == 404

        # ── 422 validations ─────────────────────────────────────────────────
        for missing_field in ["session_id", "event_type", "payload", "client_ts"]:
            body = {**valid_body}
            del body[missing_field]
            r = await client.post(f"/api/v1/restaurants/{slug}/events", json=body)
            assert r.status_code == 422, f"missing {missing_field!r} should be 422, got {r.status_code}"

        r = await client.post(
            f"/api/v1/restaurants/{slug}/events",
            json={**valid_body, "event_type": "not_a_real_event"},
        )
        assert r.status_code == 422, "invalid event_type should be 422"

        r = await client.post(
            f"/api/v1/restaurants/{slug}/events",
            json={**valid_body, "client_ts": "not-a-date"},
        )
        assert r.status_code == 422, "bad client_ts should be 422"

        r = await client.post(
            f"/api/v1/restaurants/{slug}/events",
            json={**valid_body, "payload": {"data": "x" * (16 * 1024 + 1)}},
        )
        assert r.status_code == 422, ">16KB payload should be 422"

        # ── recommendation_shown populates analytics columns ─────────────────
        session_id = f"sess-{uuid.uuid4().hex}"
        item_id = str(uuid.uuid4())
        r = await client.post(
            f"/api/v1/restaurants/{slug}/events",
            json={
                "session_id": session_id,
                "event_type": "recommendation_shown",
                "payload": {
                    "answers": {"diet": "no_restrictions", "protein": "chicken"},
                    "ranked_ids": [item_id],
                    "scores": {item_id: 9.5},
                    "top_item_id": item_id,
                },
                "client_ts": "2026-05-26T12:00:00.000Z",
            },
        )
        assert r.status_code == 204

        async with session_factory() as verify_db:
            from sqlalchemy import select
            result = await verify_db.execute(
                select(RecommendationEvent).where(RecommendationEvent.session_id == session_id)
            )
            event = result.scalar_one_or_none()
        assert event is not None
        assert event.quiz_answers == {"diet": "no_restrictions", "protein": "chicken"}
        assert event.recommended_item_ids == [item_id]
        assert event.scores == {item_id: 9.5}

        # ── CORS preflight from Live Server succeeds ─────────────────────────
        r = await client.options(
            f"/api/v1/restaurants/{slug}/events",
            headers={
                "Origin": "http://localhost:5500",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        assert r.status_code == 200
        assert r.headers.get("access-control-allow-origin") == "http://localhost:5500"

    await engine.dispose()

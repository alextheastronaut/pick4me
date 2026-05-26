# Pick4Me

QR-code restaurant menu recommender. Diner scans a QR code, answers a few questions, gets 3–4 recommended dishes with explanations.

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) running
- [uv](https://astral.sh/uv) installed (`irm https://astral.sh/uv/install.ps1 | iex`)

---

## Start the dev environment

All commands run from the `backend/` directory.

```powershell
cd backend

# 1. Start the database
docker compose up -d

# 2. Install Python deps (first time only)
uv sync

# 3. Copy env file (first time only)
cp .env.example .env

# 4. Run migrations
uv run alembic upgrade head

# 5. Seed the database (idempotent — safe to re-run)
uv run python -m app.seed

# 6. Start the API server
uv run uvicorn app.main:app --reload
```

The API is now live at `http://127.0.0.1:8000`.

---

## Stop the environment

```powershell
docker compose down      # stop and remove containers (data is preserved in the volume)
docker compose down -v   # stop and WIPE all data
```

---

## Interactive API docs

Open `http://127.0.0.1:8000/docs` in your browser — FastAPI's built-in Swagger UI lets you try every endpoint without curl.

---

## Endpoints

### `GET /health`
```
http://127.0.0.1:8000/health
```

### `POST /api/v1/restaurants/{slug}/recommendations`

Get recommendations for a diner. The seeded restaurant slug is `golden-fork`.

**curl example:**
```powershell
curl -X POST http://127.0.0.1:8000/api/v1/restaurants/golden-fork/recommendations `
  -H "Content-Type: application/json" `
  -d '{
    "session_id": "test-session-1",
    "quiz_answers": {
      "diet": "vegan",
      "protein": "no_meat",
      "flavor": "savory",
      "appetite": "light",
      "budget": "mid"
    }
  }'
```

**Quiz answer options:**

| Question | Key | Valid answers |
|---|---|---|
| Dietary restrictions | `diet` | `vegan`, `vegetarian`, `gluten_free`, `no_restrictions` |
| Preferred protein | `protein` | `chicken`, `beef`, `fish`, `no_meat` |
| Flavor profile | `flavor` | `spicy`, `sweet`, `savory`, `mild` |
| Appetite | `appetite` | `light`, `hearty`, `adventurous`, `comforting` |
| Budget | `budget` | `budget`, `mid`, `splurge` |

You can send any subset of questions — unanswered ones have no effect on scoring.

---

## Inspect the database

```powershell
docker exec -it backend-db-1 psql -U pick4me -d pick4me
```

Useful queries:

```sql
-- All menu items with their tags
SELECT mi.name, string_agg(t.key, ', ' ORDER BY t.key) AS tags
FROM menu_items mi
JOIN menu_item_tags mit ON mit.menu_item_id = mi.id
JOIN tags t ON t.id = mit.tag_id
GROUP BY mi.name
ORDER BY mi.name;

-- Quiz questions and answers
SELECT qq.key, qq.prompt, qa.key AS answer_key, qa.label
FROM quiz_questions qq
JOIN quiz_answers qa ON qa.question_id = qq.id
ORDER BY qq.order_index, qa.order_index;

-- Recent recommendation events
SELECT session_id, quiz_answers, recommended_item_ids, created_at
FROM recommendation_events
ORDER BY created_at DESC
LIMIT 10;
```

---

## Run the test suite

Tests run against a separate `pick4me_test` database. Create it once:

```powershell
docker exec backend-db-1 psql -U pick4me -c "CREATE DATABASE pick4me_test;"
```

Then run tests:

```powershell
cd backend
uv run pytest -v
```

---

## Project layout

```
backend/
  app/
    main.py            # FastAPI app + lifespan
    models.py          # SQLAlchemy ORM models (7 tables)
    quiz_config.py     # Answer → tag boost/exclude mapping (edit to tune recommendations)
    recommender.py     # Scoring algorithm
    seed.py            # Sample data: The Golden Fork
    routers/
      recommendations.py  # POST /api/v1/restaurants/{slug}/recommendations
  alembic/             # DB migrations
  tests/
    test_recommender.py
```

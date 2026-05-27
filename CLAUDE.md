# Pick4Me — Claude Context

## What this is
A QR-code restaurant menu recommender. Diner scans a QR code, answers ~5 quiz questions about preferences and dietary restrictions, and receives 3–4 recommended menu items with short explanations.

## Production URLs

| Service | URL |
|---|---|
| Frontend | https://brilla.alextheastronaut.workers.dev/osun-grill |
| Backend API | https://pick4me.fly.dev |
| Health check | https://pick4me.fly.dev/health |
| Database | Neon — ep-proud-queen-akx6qgup (project: pick4me) |
| Uptime monitoring | UptimeRobot (2 monitors, 5-min checks, alerts → alextheastronaut@gmail.com) |

## Deploy commands

```bash
# Backend — from repo root (flyctl must be logged in)
fly deploy --app pick4me --config fly.toml

# Frontend — auto-deploys on every push to master via Cloudflare/Wrangler

# Run migrations against Neon (from backend/)
DATABASE_SYNC_URL="..." uv run alembic upgrade head

# Regenerate QR code
uv run --with "qrcode[pil]" scripts/make_qr.py <url> qr-osun-grill.png
```

## If something breaks

1. **Check Fly.io logs:** `fly logs --app pick4me`
2. **Check health endpoint:** `curl https://pick4me.fly.dev/health`
3. **Check Neon dashboard:** https://console.neon.tech — verify the `pick4me` project is active and not suspended
4. **Check UptimeRobot:** https://uptimerobot.com — review alert history
5. **Check recent events in Neon:**
   ```sql
   SELECT client_meta->>'event_type', count(*), max(created_at)
   FROM recommendation_events
   WHERE created_at > now() - interval '1 hour'
   GROUP BY 1 ORDER BY 3 DESC;
   ```
6. **Redeploy backend:** `fly deploy --app pick4me --config fly.toml`
7. **Redeploy frontend:** push any commit to master — Cloudflare auto-deploys

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12 · FastAPI · SQLAlchemy 2 (async) · Alembic · asyncpg |
| Database | Neon Postgres (free tier) |
| Frontend | Single-file HTML · Cloudflare Workers (static assets via wrangler) |
| Storage | S3 for menu item images — **not wired yet** |
| Deployment | Fly.io (shared-cpu-1x, 256 MB, region sjc) — **not Lambda** |

## Repo layout

```
/
├── backend/          # FastAPI app
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── quiz_config.py   # answer→tag effect mapping (hardcoded dict)
│   │   ├── recommender.py
│   │   ├── seed.py
│   │   └── routers/
│   │       ├── recommendations.py
│   │       └── events.py    # POST /api/v1/restaurants/{slug}/events
│   ├── alembic/
│   ├── alembic.ini
│   ├── pyproject.toml
│   └── docker-compose.yml
├── frontend/
│   └── osun-grill.html   # Phase 1 single-file demo (wired to events endpoint)
├── web/              # Next.js app (Phase 2+, not yet built)
├── CLAUDE.md
└── README.md
```

## Events contract (Phase 1)

**Endpoint:** `POST /api/v1/restaurants/{slug}/events`  
**Response:** 204 No Content  
**Allowed `event_type` values:**

| event_type | fired when |
|---|---|
| `view_screen` | any screen transition (debounced 200 ms) |
| `quiz_started` | quiz begins; payload `{ entry_point: "landing"\|"menu"\|"staff"\|"retry" }` |
| `quiz_answer` | option selected; payload `{ question, value, action? }` |
| `quiz_checkpoint_choice` | checkpoint button; payload `{ choice: "now"\|"top3"\|"more" }` |
| `recommendation_shown` | result displayed; payload includes `answers`, `ranked_ids`, `scores` |
| `menu_clickthrough` | "View full menu" tapped; payload `{ from_screen, item_id, item_name }` |
| `retry_clicked` | retry button; payload `{ from_style }` |
| `feedback_submitted` | feedback form submitted; payload `{ rating, comment, item_id, style }` |
| `language_changed` | language toggled; payload `{ lang, from_screen }` |
| `quiz_abandoned` | tab hidden mid-quiz; payload `{ step, question_key, answers_so_far }` |

For `recommendation_shown`, the backend also indexes `payload.answers → quiz_answers`, `payload.ranked_ids → recommended_item_ids`, and `payload.scores → scores` for cheap SQL analytics.

Storage: events are stored in `recommendation_events` with `client_meta` JSONB holding `{ event_type, client_ts, language, payload }`. Non-recommendation rows use `{}` / `[]` sentinels for the NOT NULL analytics columns.

**Override API base in prod:** set `window.PICK4ME_API_BASE` before the script loads.

## Roadmap

| Phase | What |
|---|---|
| **Phase 1** ✅ | Single-file HTML demo wired to event-tracking endpoint. Pilot O'Sun Grill. |
| **Phase 2** | Serve menu data from backend. Schema reconciliation (demo's 7 Qs vs backend's 5). |
| **Phase 3** | Server-side recommendations via `POST /recommendations`. Next.js frontend for restaurant #2. |

## Naming conventions
- Python: `snake_case` for everything; no abbreviations
- URL slugs: `kebab-case` (e.g., `golden-fork`)
- DB primary keys: UUID (`gen_random_uuid()`)
- Timestamp columns: `_at` suffix, `timestamptz`
- Tag keys: `snake_case` strings (e.g., `gluten_free`, `contains_dairy`)

## Recommendation algorithm shape

1. **Parse answers** → collect `boost_tags` and `exclude_tags` from `quiz_config.ANSWER_EFFECTS`
2. **Hard filter** — drop any menu item whose tags intersect `exclude_tags`
3. **Score** remaining items:
   - Sum of `menu_item_tags.weight` for each matching boost tag
   - `+ 0.5 × popularity_score`
   - `+ 1.0` if `is_signature`
4. **Top-N** (default 4) with reason strings:
   - Matched boost tag → `"matches your {tag.display_name} preference"`
   - `is_signature` → `"chef's signature"`
   - `popularity_score > 7.0` → `"popular pick"`

The mapping lives entirely in `app/quiz_config.py` as a plain Python dict. No `answer_effects` table.

## Guardrails
- No premature abstraction. Three similar lines beats a new helper.
- No error handling for impossible cases. Trust SQLAlchemy and FastAPI guarantees.
- No comments that explain what the code does. Only add a comment when the WHY is non-obvious.
- Validate only at system boundaries (request bodies, external APIs).
- Alembic owns DDL. Never call `Base.metadata.create_all` in application code.

## NOT building (intentionally out of scope)
- Auth, user accounts, sessions beyond an anonymous `session_id` cookie
- Redis or any other cache layer
- A served config table (quiz config is hardcoded in `quiz_config.py`)
- DynamoDB or any NoSQL store
- AWS Lambda or any serverless compute
- Admin UI
- S3 image upload wiring (deferred)
- Row-level security (RLS)

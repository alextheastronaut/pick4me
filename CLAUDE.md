# Pick4Me — Claude Context

## What this is
A QR-code restaurant menu recommender. Diner scans a QR code, answers ~5 quiz questions about preferences and dietary restrictions, and receives 3–4 recommended menu items with short explanations.

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12 · FastAPI · SQLAlchemy 2 (async) · Alembic · asyncpg |
| Database | Postgres 16 (local Docker; Neon/Supabase for prod later) |
| Frontend | Next.js 15 (App Router) · TypeScript · Tailwind CSS · deployed to Vercel |
| Storage | S3 for menu item images — **not wired yet** |
| Deployment | Single long-running container on Fly.io or Render — **not Lambda** |

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
│   │       └── recommendations.py
│   ├── alembic/
│   ├── alembic.ini
│   ├── pyproject.toml
│   └── docker-compose.yml
├── web/              # Next.js app
│   └── lib/          # kept Next-free (no Next.js imports) for portability
├── CLAUDE.md
└── README.md
```

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

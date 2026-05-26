"""
Patch the app's global database engine to use NullPool for all tests.

NullPool creates a fresh DBAPI connection per operation and closes it
immediately after, so connections are never cached between calls. This
prevents event-loop affinity issues when pytest-asyncio gives each test
function its own event loop.

We patch at import time (conftest load) so the fix applies before any
test or fixture runs:
  - app.database.AsyncSessionLocal  → used by get_db() (module-scope ref)
  - app.routers.recommendations.AsyncSessionLocal → used by _write_event()
    (local binding from `from app.database import AsyncSessionLocal`)
"""
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import app.database as _db
import app.routers.recommendations as _rec
from app.settings import settings

_engine = create_async_engine(settings.database_url, poolclass=NullPool)
_session_factory = async_sessionmaker(_engine, expire_on_commit=False)

_db.AsyncSessionLocal = _session_factory
_rec.AsyncSessionLocal = _session_factory

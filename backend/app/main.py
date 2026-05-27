from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import events, recommendations
from app.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Pick4Me API", lifespan=lifespan)

_PROD_ORIGINS = [
    "https://brilla.alextheastronaut.workers.dev",
]
_DEV_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "null",  # file:// during local testing
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_PROD_ORIGINS if settings.app_env == "production" else _DEV_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

app.include_router(recommendations.router, prefix="/api/v1")
app.include_router(events.router, prefix="/api/v1")


@app.api_route("/health", methods=["GET", "HEAD"])
async def health():
    return {"status": "ok"}

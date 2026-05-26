from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import events, recommendations


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Pick4Me API", lifespan=lifespan)

# TODO: add production Vercel/Fly domain here when deploying (e.g. "https://pick4me.vercel.app")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # local dev
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "null",  # file:// during local testing
        # production (Cloudflare Pages — exact + preview subdomains)
        "https://plate-up.pages.dev",
    ],
    allow_origin_regex=r"https://plate-up(-[a-z0-9]+)?\.pages\.dev",
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

app.include_router(recommendations.router, prefix="/api/v1")
app.include_router(events.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}

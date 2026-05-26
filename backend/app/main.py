from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import recommendations


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Pick4Me API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recommendations.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}

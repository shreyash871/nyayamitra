"""NyayaMitra API entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.services.embedder import get_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the embedding model once at startup, not on first request
    get_model()
    yield


app = FastAPI(
    title="NyayaMitra API",
    description="Privacy-preserving Indian legal intelligence platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {
        "service": "NyayaMitra API",
        "docs": "/docs",
        "health": "/health",
    }

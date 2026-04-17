from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.api.v1 import auth, papers, analysis
from app.database.connection import engine, Base

app = FastAPI(title="AI Research Assistant", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router,     prefix="/api/v1/auth",   tags=["auth"])
app.include_router(papers.router,   prefix="/api/v1/papers", tags=["papers"])
# analysis endpoints: /api/v1/literature-review, /api/v1/research-gaps, etc.
app.include_router(analysis.router, prefix="/api/v1",        tags=["analysis"])


@app.on_event("startup")
async def startup():
    """Auto-create all tables on first start (skips alembic entirely)."""
    # Import all models so Base knows about them
    from app.models import user, paper, analysis as analysis_model, chat, project, proposal  # noqa: F401 — registers all tables with Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Ensure upload directory exists
    from app.core.config import get_settings
    settings = get_settings()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.FAISS_INDEX_PATH, exist_ok=True)


@app.get("/")
async def root():
    return {"status": "online", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

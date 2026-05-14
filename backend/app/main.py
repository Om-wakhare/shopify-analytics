"""
FastAPI application entry point.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, billing, kpi, search, sync, webhooks
from app.config import get_settings
from app.models.schemas import HealthResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s", settings.APP_NAME)
    # Run migrations on startup
    try:
        import subprocess, sys
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            capture_output=True, text=True
        )
        logger.info("Alembic stdout: %s", result.stdout)
        if result.returncode != 0:
            logger.error("Alembic stderr: %s", result.stderr)
    except Exception as e:
        logger.error("Migration error: %s", e)
    yield
    logger.info("Shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Shopify data ingestion pipeline for D2C analytics KPIs",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(billing.router)
app.include_router(search.router)
app.include_router(webhooks.router)
app.include_router(sync.router)
app.include_router(kpi.router)


@app.get("/health", response_model=HealthResponse, tags=["meta"])
async def health():
    return HealthResponse()

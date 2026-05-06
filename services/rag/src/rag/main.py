# main.py — FastAPI application entry point
#
# Phase 0: bare skeleton — just the app factory and a /health endpoint.
# Real endpoints (POST /answer, streaming) are added in Phase 2.
#
# LEARNING: We keep the FastAPI app creation in main.py and import it from
# here in tests. This means tests import the *exact same app object* that
# uvicorn runs — no "works in tests but breaks in prod" divergence.
from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from rag.config import settings

# LEARNING: We configure structured logging here at module level so it applies
# regardless of how the app is started (uvicorn, test runner, etc.).
# In production (Phase 8) we swap this for structlog with JSON output so log
# lines are machine-parseable by Loki / CloudWatch.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ── Lifecycle ─────────────────────────────────────────────────────────────────


# LEARNING: FastAPI 0.93+ recommends the `lifespan` context manager over the
# deprecated `@app.on_event("startup")` / `@app.on_event("shutdown")` hooks.
# The pattern uses a single async generator:
#   - code before `yield` runs at startup (open DB pools, warm caches)
#   - code after `yield` runs at shutdown (flush buffers, close connections)
# Phase 2 will add Qdrant client warm-up and connection-pool teardown here.
@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("RAG service starting up", extra={"version": settings.app_version})
    yield
    logger.info("RAG service shutting down")


# ── Application ───────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    # Disable the interactive docs in production by setting docs_url=None.
    # For development, /docs and /redoc are invaluable.
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── Routes ────────────────────────────────────────────────────────────────────


@app.get("/health", tags=["ops"])
async def health() -> dict[str, str]:
    """Liveness probe.

    Returns 200 {"status": "ok"} when the service is running.
    A richer readiness probe (checking Qdrant, Postgres, LLM reachability)
    is added in Phase 2 alongside the first real endpoint.
    """
    return {"status": "ok"}

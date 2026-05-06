# test_health.py — Phase 0 smoke test
#
# Goal: prove the test runner works and the app boots without error.
# This is deliberately minimal. Real tests for retrieval, prompts, and
# the /answer endpoint are added in Phase 2.
#
# LEARNING: We use httpx.AsyncClient with ASGITransport rather than
# FastAPI's TestClient because our app is fully async. ASGITransport
# calls the ASGI app directly in-process — no real network socket is
# opened — so tests are fast and require no running server.

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from rag.main import app


@pytest.mark.asyncio
async def test_health_returns_200() -> None:
    """The /health endpoint must return 200 with status=ok."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_content_type_is_json() -> None:
    """Sanity-check that the response is JSON, not HTML or plain text."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/health")

    assert "application/json" in response.headers["content-type"]

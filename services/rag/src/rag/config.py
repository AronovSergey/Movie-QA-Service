# config.py — application settings loaded from environment variables
#
# LEARNING: Pydantic Settings reads every field from environment variables
# automatically (field name uppercased). Fields without a default raise
# ValidationError at startup if the env var is missing — which is exactly
# what we want. "Fail loud early" beats "fail silently at request time."
#
# In production, secrets come from the environment (injected by Docker /
# Kubernetes). In local dev, they come from the .env file loaded by
# docker-compose or a `uv run --env-file .env` invocation.

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Reads variables from a .env file when running locally.
        # Docker / CI pass them as real env vars, so the file is optional.
        env_file=".env",
        env_file_encoding="utf-8",
        # Silently ignore extra env vars (avoids noise from unrelated vars
        # loaded from the shared root .env).
        extra="ignore",
    )

    # ── Service identity ───────────────────────────────────────────────────
    app_name: str = "rag-service"
    app_version: str = "0.1.0"

    # ── Qdrant ────────────────────────────────────────────────────────────
    # Phase 0: not used yet; declared here so config is discoverable.
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    # ── External APIs (Phase 1+) ──────────────────────────────────────────
    # No default → startup fails loudly if unset (once we actually use them).
    # For Phase 0 we give them empty-string defaults so the app boots without
    # real keys while the data plane isn't needed yet.
    #
    # WARNING: Change these to required fields (remove the default) as soon
    # as Phase 1 code starts calling the LLM or embedding APIs.
    anthropic_api_key: str = ""
    openai_api_key: str = ""


# Module-level singleton so all code does `from rag.config import settings`.
# FastAPI's dependency injection can also inject this for easier testing.
settings = Settings()

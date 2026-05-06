# Dockerfile — RAG service
#
# Multi-stage build:
#   Stage 1 (builder): install uv and resolve + install dependencies into
#                      a virtual environment.
#   Stage 2 (runtime): copy only the venv and source — no build tools.
#
# LEARNING: Multi-stage builds keep the final image small and free of build
# tooling (uv, pip, git). The builder stage can be cached aggressively;
# only requirements changes bust the dependency layer.
#
# Final image size target: < 200 MB (Python 3.12-slim base ≈ 130 MB + deps).

# ── Stage 1: builder ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

# Install uv — the fast Python package manager used throughout this project.
# Pin the version so builds are reproducible.
COPY --from=ghcr.io/astral-sh/uv:0.5.24 /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency manifests first so Docker can cache this layer.
# The venv is only rebuilt when pyproject.toml or uv.lock changes.
COPY pyproject.toml ./
# uv.lock is committed to git and ensures bit-for-bit reproducible installs.
# Run `uv lock` locally after adding dependencies to update it.
COPY uv.lock* ./

# Install dependencies into /app/.venv.
# --no-install-project: skip installing the rag package itself for now
# (we copy source in the next COPY and install everything together below).
RUN uv sync --frozen --no-install-project --no-dev

# Copy application source and install the rag package itself (editable-style).
COPY src/ ./src/
RUN uv sync --frozen --no-dev

# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Create a non-root user. Running as root inside a container is a security
# risk — if the container escapes, root access to the host is easier.
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copy the resolved venv from the builder (includes all dependencies + rag package).
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

# Put the venv's bin/ first on PATH so `python` and `uvicorn` resolve to it.
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

USER appuser

EXPOSE 8000

# LEARNING: We run uvicorn directly rather than via a process manager like
# gunicorn because in a container orchestration environment (Docker Compose,
# Kubernetes), the orchestrator handles restarts and scaling. One process
# per container is the idiomatic pattern.
CMD ["uvicorn", "rag.main:app", "--host", "0.0.0.0", "--port", "8000"]

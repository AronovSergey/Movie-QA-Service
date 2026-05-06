# RAG Service

Retrieval-augmented generation endpoint for Movie QA. Takes a question (and optional conversation history) and returns a grounded answer with citations.

**Phase 0:** bare skeleton — only `/health` exists.  
**Phase 2:** adds `POST /answer` with full retrieval + LLM pipeline.

## Running locally

```bash
# From services/rag/
uv sync --dev          # install all deps into .venv
uv run uvicorn rag.main:app --reload --port 8000
```

Docs available at [http://localhost:8000/docs](http://localhost:8000/docs).

## Running tests

```bash
uv run pytest
```

## Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `QDRANT_HOST` | No | `localhost` | Qdrant host |
| `QDRANT_PORT` | No | `6333` | Qdrant REST port |
| `ANTHROPIC_API_KEY` | Phase 1+ | — | Anthropic API key |
| `OPENAI_API_KEY` | Phase 1+ | — | OpenAI API key (for embeddings) |

## Docker

```bash
docker build -t movieqa-rag .
docker run -p 8000:8000 --env-file ../../.env movieqa-rag
```

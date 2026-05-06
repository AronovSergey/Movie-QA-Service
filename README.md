# Movie QA Service

A movie and TV Q&A service powered by RAG (Retrieval-Augmented Generation). Ask questions like "Who directed Dune?", "What is Interstellar about?", or "Recommend something like Blade Runner" and get grounded, cited answers.

Built as a learning project following a phased implementation plan. See [`IMPLEMENTATION_PLAN.md`](./IMPLEMENTATION_PLAN.md) for the full roadmap.

---

## Architecture overview

The system is split into two planes that share data but never share request handling:

```
┌──────────────────────────────────────────────────────────────┐
│                      REQUEST PLANE                            │
│  (user-facing, synchronous)                                   │
│                                                               │
│  Browser                                                      │
│    └── Nginx :80                                              │
│          ├── auth    :8081  (signup / login / JWT)            │
│          ├── chat    :8082  ──► RAG service :8000             │
│          └── catalog :8083  (movie search & detail)           │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                    INGESTION PLANE                            │
│  (background, asynchronous)                                   │
│                                                               │
│  scheduler :8084                                              │
│      └──► RabbitMQ (ingest.requested)                         │
│               └──► Collector  ← TMDB + Wikipedia              │
│                       └──► RabbitMQ (movie.normalized)        │
│                                └──► Indexer                   │
│                                       ├── Postgres (catalog)  │
│                                       └── Qdrant (vectors)    │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                    SHARED DATA PLANE                          │
│  Postgres 16  ·  Redis 7  ·  Qdrant  ·  RabbitMQ 3           │
└──────────────────────────────────────────────────────────────┘
```

**Rule:** the two planes never share request handling. They share data only.

---

## Services

### `Nginx` — port 80 — the front door
Every request from the React frontend hits Nginx first. Responsibilities:
- **Routing** — `/auth/**` → auth, `/chat/**` → chat, `/catalog/**` → catalog
- **JWT validation** — in Phase 5, uses the `auth_request` module: Nginx calls the auth service to validate the token and injects the returned `X-User-Id` header downstream. No service ever parses a JWT itself.
- **CORS** — one place to configure allowed origins
- **SSE support** — `proxy_buffering off` on the chat route enables Phase 6 streaming

Config lives in `infra/nginx/nginx.conf`. See [ADR-0001](./docs/adr/0001-nginx-as-api-gateway.md) for why Nginx over Spring Cloud Gateway.

---

### `auth` — port 8081 — identity
Owns everything about users and tokens:
- `POST /auth/signup` — creates a user, hashes the password with bcrypt
- `POST /auth/login` — validates password, issues a JWT access token + HTTP-only refresh cookie
- `POST /auth/refresh` — exchanges a valid refresh token for a new access token

No other service ever touches passwords or issues tokens.

---

### `chat` — port 8082 — conversations
The main service users interact with. Owns:
- Conversation and message persistence in Postgres (`chat` schema)
- The question flow: receives a user's question → builds conversation history → calls the RAG service → persists the answer → returns it

Does no AI work itself — delegates entirely to the RAG service.

---

### `catalog` — port 8083 — movie data (read-only)
A clean, read-only API over the `movies`, `people`, `credits`, and `genres` tables. Used by the frontend for search and detail pages.

Writes only arrive from the ingestion plane — never from the request plane.

---

### `scheduler` — port 8084 — background trigger
Fires a cron every 8 hours and publishes `ingest.requested` to RabbitMQ. Also exposes `POST /admin/trigger-ingestion` (admin token required) for manual runs.

Does no data work itself — it only pulls the trigger.

---

### `rag` — port 8000 — retrieval + LLM (Python / FastAPI)
The AI core of the system:
1. Embeds the user's question
2. Queries Qdrant for the top-K most relevant chunks
3. Builds a prompt with the retrieved context
4. Calls Claude (Anthropic) and streams the answer back

Never called directly by the user — only by the `chat` service.

---

### `collector` — Python worker (Phase 7)
First stage of the ingestion plane. Consumes `ingest.requested` from RabbitMQ:
1. Fetches movie and people data from the TMDB API
2. Enriches with biographies from Wikipedia
3. Normalizes into a `NormalizedMovie` schema (with `schema_version`)
4. Publishes `movie.normalized` to RabbitMQ

**Boundary:** imports TMDB client, Wikipedia client, normalizer. Never imports the chunker, embedder, or Qdrant client.

---

### `indexer` — Python worker (Phase 7)
Second stage of the ingestion plane. Consumes `movie.normalized` from RabbitMQ:
1. Chunks prose fields (overviews, biographies)
2. Embeds chunks with OpenAI `text-embedding-3-small`
3. Upserts structured records to Postgres (`catalog` schema)
4. Upserts embeddings + metadata to Qdrant
5. Publishes `movie.indexed` on success

**Boundary:** imports chunker, embedder, Postgres client, Qdrant client. Never imports TMDB or Wikipedia clients.

Every operation is idempotent — safe to re-run on the same input.

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite, TypeScript, Tailwind, shadcn/ui, TanStack Query |
| API Gateway | Nginx 1.27 (`auth_request` pattern) |
| Backend services | Spring Boot 3.5, Spring Data JPA, Flyway, Lombok |
| RAG service | FastAPI, Pydantic, asyncpg, qdrant-client, anthropic |
| Collector | Python 3.12, aio-pika, httpx, aiolimiter |
| Indexer | Python 3.12, aio-pika, qdrant-client, openai |
| Vector DB | Qdrant |
| Relational DB | Postgres 16 (schema-per-service) |
| Cache / sessions | Redis 7 |
| Message broker | RabbitMQ 3 |
| Observability | OpenTelemetry, Prometheus, Grafana, Langfuse, Loki |

---

## Local development

### Prerequisites

| Tool | Version | Install |
|---|---|---|
| Docker Desktop | latest | [docker.com](https://www.docker.com) |
| Java | 21 (Temurin) | [adoptium.net](https://adoptium.net) |
| Node.js | 20+ | `nvm install 20` |
| Python | 3.12 | `uv python install 3.12` |
| uv | latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |

### First-time setup

```bash
# 1. Copy env file and fill in API keys
cp .env.example .env

# 2. Start the data plane (Postgres, Redis, Qdrant, RabbitMQ, Nginx)
docker compose --profile infra up -d

# 3. Verify all services are healthy
docker compose ps
```

---

## Project layout

```
.
├── services/
│   ├── auth/        # Spring Boot — JWT, users
│   ├── chat/        # Spring Boot — conversations, RAG proxy
│   ├── catalog/     # Spring Boot — movie/people read API
│   ├── scheduler/   # Spring Boot — cron + admin trigger
│   ├── rag/         # FastAPI — retrieval + LLM
│   ├── collector/   # Python — fetch + normalize (Phase 7)
│   └── indexer/     # Python — chunk + embed + write (Phase 7)
├── frontend/        # React + Vite + TypeScript
├── infra/
│   ├── nginx/       # nginx.conf
│   └── postgres/    # init SQL (schema creation)
├── docs/
│   ├── adr/         # Architecture Decision Records
│   └── learnings/   # Dev notes and lessons learned
├── eval/            # RAG evaluation suite (Phase 8)
├── notebooks/       # Phase 1 Jupyter notebooks
├── docker-compose.yml
└── .env.example
```

---

## Architecture Decision Records

Significant decisions are documented in [`docs/adr/`](./docs/adr/). Read these to understand *why* the system is shaped the way it is, not just *what* it does.

| ADR | Decision |
|---|---|
| [0001](./docs/adr/0001-nginx-as-api-gateway.md) | Nginx as API gateway over Spring Cloud Gateway |

---

## Implementation phases

See [`IMPLEMENTATION_PLAN.md`](./IMPLEMENTATION_PLAN.md) for the full phased plan.

| Phase | Goal | Status |
|---|---|---|
| 0 | Project skeleton — repo, infra, service scaffolds | 🔄 In progress |
| 1 | RAG works in a Jupyter notebook | ⬜ Pending |
| 2 | RAG wrapped in a FastAPI service | ⬜ Pending |
| 3 | Chat service with Postgres persistence | ⬜ Pending |
| 4 | React frontend | ⬜ Pending |
| 5 | Auth + Nginx JWT validation | ⬜ Pending |
| 6 | Streaming responses (SSE) | ⬜ Pending |
| 7 | Catalog service + ingestion plane (Collector + Indexer) | ⬜ Pending |
| 8 | Observability + eval suite | ⬜ Pending |

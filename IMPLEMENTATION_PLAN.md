# Implementation Plan

A phased, ship-something-every-week approach to building the Movie QA service. Each phase ends with a working, demoable system. Resist the urge to skip ahead — the order is deliberate.

## Guiding principles

- **Vertical slices, not horizontal layers.** Build one feature end-to-end before moving on. Don't build all the auth, then all the chat, then all the AI. Build a minimal version of the *whole* path, then improve it.
- **Working > complete.** A janky chat with 50 movies that returns real answers is worth more than a half-built microservices cluster with no AI yet.
- **Test what would hurt to break.** RAG quality, auth flows, and idempotency. Skip exhaustive tests on glue code.
- **Commit early, commit often.** Each phase has a tag in git so you can compare diffs and remember what you changed when.
- **Cost discipline.** Use cheap models in dev. Cache aggressively. Run an offline eval rarely.

## Pre-flight: tools to install before phase 0

- **Docker Desktop** (or Docker Engine + Compose on Linux)
- **Node.js 20+** (use `nvm` or `fnm` to manage versions)
- **Java 21** (use `sdkman` for easy install)
- **Python 3.12** (use `uv` — modern, fast, replaces pip+venv+pyenv)
- **Maven** (or use the Maven wrapper `./mvnw` that comes with Spring Boot projects)
- **An API key** for Anthropic or OpenAI (Anthropic recommended for cost; sign up at console.anthropic.com)
- **A TMDB account** for an API key (themoviedb.org/settings/api — free, instant)

Verify each works before continuing:

```bash
docker --version
node --version
java --version
python --version
uv --version
```

---

## Phase 0 — Project skeleton (1-2 days)

**Goal:** repo exists, runs, has CI. Nothing functional yet.

### Steps

1. **Create the monorepo.** One repo, multiple services in subfolders. Init git.
2. **Write `docker-compose.yml`** with just Postgres, Redis, Qdrant, RabbitMQ. Bring it up. Verify each is reachable.
3. **Scaffold each service folder** with a hello-world: Spring Boot services with `start.spring.io`, FastAPI services with `uv init`, frontend with `npm create vite@latest`.
4. **Set up GitHub Actions CI.** One workflow that runs lint + tests on every push. Even with empty test suites, the green checkmark builds the habit.
5. **Add a `Makefile`** at the root with `make up`, `make down`, `make test`, `make logs`. You'll thank yourself later.
6. **Pre-commit hooks.** `pre-commit` Python tool, with hooks for Java formatting (Spotless), Python formatting (ruff), and TypeScript formatting (prettier).

### Tests at this phase

One trivial test per service, just to prove the test runner works:

- Spring Boot: a `@SpringBootTest` that boots the context successfully
- FastAPI: a `pytest` test that hits `/health` and gets `200`
- React: a Vitest test asserting `1 + 1 === 2`

### Done when

- `docker-compose up -d` brings up the data plane.
- Every service starts without error.
- `make test` runs all test suites and passes.
- CI is green on the main branch.

---

## Phase 1 — RAG works in a notebook (3-5 days)

**Goal:** prove the AI side of the project is achievable. No services, no API. Just Python in a Jupyter notebook.

This is the most important phase. Everything that follows is plumbing for what you build here.

### Steps

1. **Pick 50 movies** from TMDB. Hard-code their IDs. Pull title, overview, year, genres, runtime, and credits via the TMDB API.
2. **Pull biographies** from Wikipedia for the top 5 directors among those movies.
3. **Write structured records to Postgres.** Define minimal `movies`, `people`, `credits` tables.
4. **Chunk prose fields** — overviews and biographies. Use `RecursiveCharacterTextSplitter` from `langchain-text-splitters` (it's a 1KB dependency, just for the splitter — don't pull all of LangChain).
5. **Embed each chunk** with OpenAI `text-embedding-3-small`. Store text + embedding + metadata (movie_id, source, chunk_index) in Qdrant.
6. **Build the retrieval function.** Take a question, embed it, query Qdrant for top-5 chunks, return them with metadata.
7. **Build the prompt.** System message instructing the LLM to answer only from context and admit ignorance otherwise. User message containing context + question.
8. **Call Claude Haiku.** Print the answer.
9. **Iterate.** Try 20 different questions. Some will work great. Some won't. Tweak chunking strategy, K (number of retrieved chunks), prompt phrasing. Each tweak teaches you something.

### Tests at this phase

- **Unit tests** for the chunking function (does it produce expected number of chunks for a known input?).
- **Integration test** that hits Qdrant with a known query and asserts the right chunk is in the top 3 results.
- **A tiny eval set** — 10 question/expected-answer pairs you write yourself in a `eval/golden.jsonl` file. Run them all at once and eyeball whether answers are reasonable. This is the seed of your real eval suite later.

### Done when

- Asking "Who directed [movie X]?" gives correct answers for all 50 movies.
- Asking "What is [movie X] about?" gives a grounded summary (not invented).
- Asking "Who directed [movie not in dataset]?" gets "I don't have information about that" — not a hallucination.
- Your eval set runs in under a minute and you can read all the answers.

### Pitfalls to avoid

- Don't pre-optimize. Fixed-size chunking is fine here. Don't reach for hybrid retrieval, reranking, or query rewriting yet. Get a baseline first.
- Don't use LangChain or LlamaIndex frameworks. Write the loop yourself in 100 lines. You need to *understand* what's happening before abstracting it away.
- Cache LLM responses to disk during development. Same question shouldn't cost twice.

**Tag the repo `phase-1-rag-works` when done.**

---

## Phase 2 — Wrap RAG in a service (2-3 days)

**Goal:** the notebook code becomes a real HTTP service.

### Steps

1. **Move notebook code** into `services/rag/`. Organize into modules: `retrieval.py`, `prompts.py`, `llm.py`, `main.py`.
2. **Create FastAPI app** with one endpoint: `POST /answer` taking `{question: str, conversation_history?: [...]}` and returning `{answer: str, citations: [...]}`.
3. **Add Pydantic models** for request and response. Strong typing makes everything cleaner.
4. **Add a `/health` endpoint.** Returns 200 if Postgres, Qdrant, and the LLM API are all reachable.
5. **Dockerize.** Multi-stage Dockerfile, small final image.
6. **Add to `docker-compose.yml`.** RAG service starts with the rest of the stack.

### Tests at this phase

- **Unit tests** for prompt assembly (deterministic — given chunks X and question Y, expected prompt is Z).
- **Unit tests** for retrieval logic (mock Qdrant, assert correct query is built).
- **Integration test** for `/answer` using a test Qdrant instance loaded with fixture data.
- **Use `pytest-asyncio`** since FastAPI is async.
- **Aim for 70%+ coverage** on the retrieval/prompt modules. Skip coverage targets for the LLM client wrapper — testing that is mostly testing your mock.

### Done when

- `curl localhost:8000/answer -d '{"question": "Who directed Dune?"}'` returns a reasonable answer.
- The service is in `docker-compose.yml` and starts cleanly.
- Tests pass in CI.

**Tag `phase-2-rag-service`.**

---

## Phase 3 — Chat service in front (3-5 days)

**Goal:** Spring Boot service handles user-facing concerns and proxies to the RAG service. Real Postgres persistence for conversations.

### Steps

1. **Initialize Spring Boot project** in `services/chat/` (Spring Web, Spring Data JPA, Validation, PostgreSQL driver, Lombok).
2. **Define `Conversation` and `Message` entities.** Use Liquibase or Flyway for migrations.
3. **REST endpoints:**
   - `POST /conversations` — create new conversation
   - `GET /conversations` — list user's conversations
   - `GET /conversations/{id}/messages` — fetch messages
   - `POST /conversations/{id}/messages` — send a question, returns the answer
4. **Implement the question flow** in a service class:
   - Persist user message
   - Build conversation history (last N messages) for context
   - Call RAG service via `RestTemplate` or `WebClient`
   - Persist assistant message with citations
   - Return both messages
5. **Add OpenAPI docs** with Springdoc. Visit `/swagger-ui.html` and verify endpoints.
6. **No auth yet** — accept a `X-User-Id` header for now. Auth comes in phase 5.

### Tests at this phase

- **Unit tests** for the chat service class (mock the RAG client, mock the repository).
- **Integration tests** with **Testcontainers** — spin up a real Postgres in a container, run the test, tear it down. This is the single most valuable testing pattern in Java backend; learn it now.
- **API tests** with `@SpringBootTest` + `MockMvc` for the controller layer.
- **Contract test** for the RAG service call: build a stub server, assert the exact request body sent.

### Done when

- You can create a conversation, send messages, and get answers persisted in Postgres.
- Restarting the chat service preserves conversation history.
- Test coverage on service classes is healthy (80%+).
- CI runs Postgres in a Testcontainer and all integration tests pass.

**Tag `phase-3-chat-service`.**

---

## Phase 4 — React frontend (3-4 days)

**Goal:** an actual chat UI you can share screenshots of.

### Steps

1. **Vite + React + TypeScript + Tailwind + shadcn/ui** in `frontend/`.
2. **Routes:** `/` (chat), `/conversations` (history sidebar).
3. **TanStack Query** for all server state. No `useState` for data that lives on the server.
4. **Components:** `ConversationList`, `ChatThread`, `MessageBubble`, `MessageInput`.
5. **API client module** (`src/api/`) with typed functions wrapping fetch. Use Zod for runtime validation of responses.
6. **Render Markdown** in assistant messages with `react-markdown`. The LLM emits markdown.
7. **Render citations** as clickable chips below each assistant message.
8. **No auth yet** — hard-code a user ID in `localStorage`.

### Tests at this phase

- **Component tests** with Vitest + Testing Library for the bubble, list, input components.
- **Integration test** that mocks the API and asserts the chat flow works end-to-end (type, submit, see response).
- **Skip E2E tests for now** — Playwright comes in phase 7.

### Done when

- You can open the app in a browser, ask questions, see answers stream in (well, appear after a beat — true streaming is phase 6).
- Conversations persist across page refresh.
- It looks decent. Not pretty, decent.

**Tag `phase-4-frontend`.**

---

## Phase 5 — Auth & Nginx entry point (3-5 days)

**Goal:** real users, real boundaries. Single entry point via Nginx instead of a dedicated gateway service. See ADR-0003 for why.

### Steps

1. **Auth service** (`services/auth/`):
   - Spring Boot + Spring Security + JJWT library
   - `POST /auth/signup`, `POST /auth/login`, `POST /auth/refresh`
   - Bcrypt password hashing
   - JWT signed with HS256 (use a strong secret from env). Document the choice of HS256 (shared secret) vs RS256 (public/private key) in an ADR — for a learning project HS256 is simpler.
2. **Shared `auth-common` module** (Maven module under `libs/auth-common/` or similar):
   - `JwtAuthenticationFilter` — Spring Security filter that validates Bearer tokens
   - `SecurityConfig` — base configuration, services extend it
   - `@CurrentUserId` annotation + argument resolver for controllers
   - Each service (`chat`, `catalog`) imports this module instead of duplicating auth code
3. **Nginx setup** (`infra/nginx/nginx.conf`):
   - Routes: `/api/auth/*` → auth service, `/api/chat/*` → chat service, `/api/catalog/*` → catalog service, `/` → frontend
   - Sets `X-Forwarded-For`, `X-Forwarded-Proto`, `X-Real-IP` headers on upstream requests
   - Enables gzip compression on responses
   - Configures `limit_req` zones for blunt per-IP rate limiting
   - In dev: serves the Vite dev server via proxy. In prod: serves the built frontend as static files.
4. **TLS in production:** Let's Encrypt + certbot. For local dev, plain HTTP is fine.
5. **Update Spring Boot services** to use the `auth-common` filter and to read user identity from the validated JWT (not from request headers — JWT is the source of truth).
6. **React auth flow:** signup, login, store JWT in memory (not localStorage — XSS risk), refresh-token cookie HTTP-only. All API calls go to `/api/*` which Nginx routes to the right service.

### Tests at this phase

- **Auth service:** test signup creates user, login returns valid JWT, expired tokens rejected.
- **`auth-common` filter:** test that missing/expired/tampered tokens are rejected with 401, valid tokens populate `SecurityContext`.
- **Nginx routing:** integration test using Testcontainers for Nginx, verifying each route reaches the correct upstream.
- **Security tests:** confirm wrong passwords fail, confirm token tampering fails, confirm an authenticated user cannot access another user's conversations.
- **End-to-end happy path test:** signup → login → send message → get answer. Run this in CI through Nginx, not directly to services.

### Done when

- Multiple users can sign up and have separate conversation histories.
- A request without a token is rejected by the receiving service with 401.
- All requests from the frontend go through Nginx (`/api/*` paths only).
- The `auth-common` module is shared cleanly — no duplicated JWT code across services.
- TLS works locally with a self-signed cert (and you know how to swap in Let's Encrypt for production).

**Tag `phase-5-auth`.**

---

## Phase 6 — Streaming responses (2-3 days)

**Goal:** tokens appear progressively, not in a 4-second freeze.

### Steps

1. **RAG service:** change the `/answer` endpoint to return a `StreamingResponse` of newline-delimited JSON or SSE.
2. **Chat service:** add a streaming endpoint `POST /conversations/{id}/messages/stream` that returns SSE. It calls the RAG service streaming endpoint and forwards chunks. Use Spring's `SseEmitter`.
3. **React:** use `fetch` with a `ReadableStream` to read the SSE stream and append tokens to the message bubble as they arrive.
4. **Persist the message after the stream completes** — chat service buffers the full answer while streaming, then writes to Postgres at the end.

### Tests at this phase

- **Unit tests** verifying the SSE format is correct (ends with the right markers).
- **Integration test** that consumes a stream from the chat service and reassembles it correctly.
- **Frontend test** that mocks an SSE response and asserts UI renders progressively.

### Done when

- Answers feel responsive. Tokens appear within ~500ms of submitting.
- A network drop mid-stream is handled gracefully (error displayed, no orphan messages in DB).

**Tag `phase-6-streaming`.**

---

## Phase 7 — Catalog service & integration plane (1 week)

**Goal:** production-shaped data ingestion. The integration plane separates from the request plane and is built as two services from the start: Collector (fetch + normalize) and Indexer (chunk + embed + write). See ADR-0004 for the rationale.

### Steps

1. **Catalog service** (`services/catalog/`): read-only Spring Boot API for movie/person detail pages and search. Owns the `movies`, `people`, `credits`, `genres` tables.
2. **Refactor the RAG service:** instead of querying Postgres directly for movie metadata, it can either query Postgres directly (simpler) or call the catalog service's API (cleaner). Pick one and document the choice.
3. **Define the wire format first.** Create the `NormalizedMovie` Pydantic model with `schema_version: int = 1` in a shared module. This is the contract between Collector and Indexer.
4. **Collector service** (`services/collector/`):
   - Steps 1-3 of the pipeline: fetch from TMDB, enrich from Wikipedia, normalize.
   - Consumes `ingest.requested` from RabbitMQ.
   - Publishes `movie.normalized` events with the `NormalizedMovie` payload + standard event envelope.
   - **Imports allowed:** TMDB client, Wikipedia client, normalizer logic, `NormalizedMovie` schema. **Imports forbidden:** chunker, embedder, Qdrant client.
   - Strict rate limiter on TMDB calls (use `aiolimiter`, ~30 req/10s to stay safely under TMDB's 40 req/10s limit).
5. **Indexer service** (`services/indexer/`):
   - Steps 4-7: chunk prose, embed chunks, upsert to Postgres, upsert to Qdrant.
   - Consumes `movie.normalized` from RabbitMQ.
   - Publishes `movie.indexed` events on success (lets future consumers attach).
   - **Imports allowed:** chunker, embedder, Postgres client, Qdrant client, `NormalizedMovie` schema. **Imports forbidden:** TMDB client, Wikipedia client.
   - Idempotent upserts: Postgres `INSERT ... ON CONFLICT (tmdb_id) DO UPDATE`; Qdrant `upsert` with deterministic point IDs (`tmdb_{movie_id}_{source}_{chunk_index}`).
6. **Scheduler service** (`services/scheduler/`): tiny Spring Boot service with `@Scheduled(cron = "0 0 */8 * * *")`. Publishes `ingest.requested` to RabbitMQ. Also exposes `POST /admin/trigger-ingestion` for manual runs (gated by separate admin auth).
7. **Dead-letter queues:** configure RabbitMQ so messages that fail 3 times go to a DLQ — separate DLQs for `ingest.requested` and `movie.normalized` so you can tell which stage failed. Add Grafana panels showing each DLQ's depth.
8. **Distributed tracing:** OpenTelemetry traces propagate `correlation_id` from `ingest.requested` through `movie.normalized` to `movie.indexed`. End-to-end traces span all three services.

### Tests at this phase

- **Idempotency tests** (mandatory for both services): re-process the same event, assert no duplicate rows or chunks. Run the full pipeline twice, assert identical state.
- **Import boundary tests:** static analysis (e.g., a small custom test that grep's imports) confirms Collector doesn't import chunker/embedder, Indexer doesn't import TMDB/Wikipedia. Architectural rules enforced as tests.
- **Contract test for `movie.normalized`:** the Indexer's input schema accepts the Collector's output schema. CI catches schema drift.
- **Cross-service integration test:** publish `ingest.requested`, wait, assert `movie.indexed` is published and data is in Postgres + Qdrant. Use Testcontainers for the broker.
- **Failure isolation test:** simulate TMDB returning 503, assert messages land in `ingest.requested.dlq` after 3 retries while the Indexer continues processing existing `movie.normalized` queue.

### Done when

- Both services run independently in `docker-compose.yml` with their own resource limits.
- The scheduler fires every 8 hours and ingestion completes end-to-end without manual intervention.
- A manual admin trigger works.
- Failed messages in either DLQ are visible in Grafana but don't block the rest of the pipeline.
- Re-running the pipeline produces identical state (idempotent across both services).
- 5,000+ movies in the catalog. RAG quality remains good or improves.
- Distributed traces show the full chain: `ingest.requested` → Collector → `movie.normalized` → Indexer → Postgres/Qdrant.

**Tag `phase-7-integration-plane`.**

---

## Phase 8 — Quality & observability (1 week)

**Goal:** know when things are bad. Improve them systematically.

### Steps

1. **Build a real eval set.** 50-100 question/expected-answer pairs covering: factual lookups, recommendations, comparisons, "I don't know" cases. Store as JSONL in `eval/`.
2. **Eval runner:** a Python script that runs every question through your system, scores the answer (LLM-as-judge with a separate prompt + manual review for tricky cases), and outputs a score report.
3. **Run evals on every meaningful change.** Add a `make eval` target.
4. **OpenTelemetry instrumentation** in every service. Traces flow from React → gateway → chat → RAG → LLM API.
5. **Prometheus + Grafana** for metrics: request rates, latencies (p50/p95/p99), error rates, queue depths.
6. **Langfuse for LLM traces.** Captures every prompt, every retrieved chunk, every response, every cost. Self-host in Docker.
7. **Logs:** structured JSON logs with `trace_id` correlation across services. Use Loki + Promtail for aggregation.
8. **Alerts:** queue depth > N, error rate > X%, p99 latency > Y ms. Send to your email or Slack.

### Tests at this phase

- **Eval set runs in CI** on every PR. PR that drops eval score by >5% fails.
- **Load test** with `k6` or `locust`. 100 concurrent users for 5 minutes. Identify bottlenecks.

### Done when

- You have a number that says how good RAG is. You watch it over time.
- You have dashboards you actually look at.
- A real failure (e.g., killing Postgres) shows up clearly in the alerts.

**Tag `phase-8-observability`.**

---

## Phase 9 — Quality improvements you've earned the right to make (open-ended)

**Goal:** now that you can measure, improve.

Pick from this menu based on what your eval reveals:

- **Hybrid retrieval:** add SQL-based retrieval for structured questions ("movies Nolan directed after 2010"). Route via intent classification.
- **Reranking:** add `bge-reranker-base` between vector search and LLM. Measure the eval delta.
- **Better chunking:** document-aware chunks tailored to the source type (overview chunks vs. review chunks vs. biography chunks).
- **Query rewriting:** use a cheap LLM to rephrase or expand the user's question before retrieval.
- **Conversation context:** include recent messages in retrieval (not just the latest question).
- **Multi-step retrieval (agentic):** let the LLM call retrieval as a tool when it needs more info.

Each of these is a real research-flavored project and worth a tag of its own.

---

## Best practices to maintain throughout

### Testing pyramid

- **Lots of unit tests** (fast, run on every save). Pure functions, no I/O.
- **A meaningful number of integration tests** (Testcontainers for Java; pytest fixtures for Python). Real DB, real broker. These catch the most real bugs.
- **A handful of E2E tests** (Playwright). Just the critical user journeys. Slow, brittle, but catch what nothing else does.

### Code quality

- **Linters configured per language:** ESLint + Prettier for TS, Spotless + Checkstyle for Java, Ruff for Python.
- **No warnings in CI.** Zero. Get to zero, stay at zero.
- **PR template** with a checklist: tests added, docs updated, eval still passes.

### Git hygiene

- **Conventional commits:** `feat:`, `fix:`, `chore:`, `docs:`, `test:`. You'll thank yourself when you read your own log in 6 months.
- **Branch per feature.** Never push directly to main.
- **Tags at phase boundaries.** Easy to compare "what did the system look like at phase 3 vs phase 5".

### Secret management

- **Never commit secrets.** Use a `.env` file ignored by git. Use `dotenv` libraries to load.
- **In CI:** GitHub Actions secrets.
- **In production (when you get there):** the cloud provider's secret manager.

### Documentation

- **Each service has its own README** explaining what it does, its endpoints, and how to run it.
- **Architecture decision records (ADRs)** in `docs/adr/`. One markdown file per significant decision: "ADR-001: We chose RabbitMQ over Kafka because...". Future-you will be very grateful.

### Cost discipline

- **Cache LLM responses during development.** A simple disk cache keyed on the prompt hash. Don't re-pay for the same answer.
- **Use the cheapest model that works.** Default to Haiku 4.5. Only escalate to Sonnet if eval scores genuinely improve.
- **Keep a `costs.md` log** with monthly totals. Stay aware.

---

## Estimated total time

Solo, evenings and weekends, with full-time job: **3-5 months** to reach end of Phase 8. Phase 9 is open-ended and could keep you busy for years. Don't sweat the timeline — the goal is learning, and rushing skips the learning.

## When to deploy publicly

Phase 6 is the earliest you'd want to show this to anyone. Phase 8 is when it's ready to be a portfolio piece. Phase 9+ is when it stops being a project and starts being a system you maintain.

Good luck. Build vertically. Test what hurts. Ship something every week.

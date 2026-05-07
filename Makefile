# Makefile — Movie QA Service
#
# Convenience targets for the most common development operations.
# Run `make help` to see all available targets.
#
# LEARNING: Makefiles are not just for C projects. They are a lingua franca
# for running project tasks — every developer knows `make <target>` regardless
# of the underlying language or toolchain. The alternative (a `scripts/`
# folder full of shell files with different conventions) is harder to discover.
#
# Prerequisites: docker, docker compose v2 (bundled with Docker Desktop),
#                Java 21 + Maven wrapper (./mvnw), uv (Python), Node 20 + npm.

# ── Configuration ─────────────────────────────────────────────────────────────

# Fail immediately if any command in a recipe returns a non-zero exit code.
# Without this, Make silently continues after a failed step.
.SHELLFLAGS := -eu -o pipefail -c
SHELL       := bash

# All targets are phony — none of them produce a file with that name.
# Without .PHONY, Make skips a target if a file of the same name exists.
.PHONY: help \
        infra-up infra-down up down logs \
        test test-java test-rag test-frontend \
        lint lint-rag lint-frontend \
        clean

# Spring Boot services that have a Maven wrapper
JAVA_SERVICES := auth chat catalog scheduler

# ── Help ──────────────────────────────────────────────────────────────────────

# LEARNING: The `help` target parses the Makefile itself for lines matching
# `## comment` and prints them as a usage guide. This keeps documentation
# next to the target, so they can't drift apart.
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' \
	  | sort

# ── Infrastructure (data plane) ───────────────────────────────────────────────

infra-up: ## Start infrastructure services (Postgres, Redis, Qdrant, RabbitMQ, Nginx)
	docker compose --profile infra up -d
	@echo "✓ Infrastructure is up. Waiting for health checks..."
	docker compose --profile infra ps

infra-down: ## Stop infrastructure services (data is preserved in named volumes)
	docker compose --profile infra down

# ── Full stack ────────────────────────────────────────────────────────────────

up: ## Start all services (infra + app services added in later phases)
	docker compose up -d

down: ## Stop all services
	docker compose down

logs: ## Tail logs from all running containers (Ctrl-C to exit)
	docker compose logs -f

# ── Tests ─────────────────────────────────────────────────────────────────────

test: test-java test-rag test-frontend ## Run all test suites

test-java: ## Run tests for all Spring Boot services
	@for svc in $(JAVA_SERVICES); do \
	  echo ""; \
	  echo "── Testing services/$$svc ──────────────────────────────"; \
	  cd services/$$svc && ./mvnw -q test && cd ../..; \
	done
	@echo ""
	@echo "✓ All Java tests passed"

test-rag: ## Run RAG service tests (pytest)
	@echo "── Testing services/rag ──────────────────────────────────"
	cd services/rag && uv run pytest -v
	@echo "✓ RAG tests passed"

test-frontend: ## Run frontend tests (Vitest)
	@echo "── Testing frontend ──────────────────────────────────────"
	cd frontend && npm test
	@echo "✓ Frontend tests passed"

# ── Lint ──────────────────────────────────────────────────────────────────────

lint: lint-rag lint-frontend ## Run all linters

lint-rag: ## Lint RAG service with ruff
	cd services/rag && uv run ruff check src/ tests/

lint-frontend: ## Lint frontend with ESLint + TypeScript typecheck
	cd frontend && npm run lint && npm run typecheck

# ── Cleanup ───────────────────────────────────────────────────────────────────

clean: ## Remove build artifacts (does NOT remove Docker volumes)
	@echo "Cleaning Java build outputs..."
	@for svc in $(JAVA_SERVICES); do \
	  cd services/$$svc && ./mvnw -q clean && cd ../..; \
	done
	@echo "Cleaning frontend build output..."
	rm -rf frontend/dist
	@echo "✓ Clean complete"

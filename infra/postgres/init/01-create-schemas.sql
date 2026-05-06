-- 01-create-schemas.sql
-- Runs once on first Postgres container startup (alphabetical order).
--
-- LEARNING: We create one schema per service rather than using the default
-- `public` schema for everything. This enforces logical boundaries at the DB
-- level — the auth service's tables live in `auth`, chat's in `chat`, etc.
-- A schema owner role per service would be the next step in a production setup,
-- but for a learning project a single superuser is fine.
--
-- See docs/adr/0004-postgres-schema-per-service.md

CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS chat;
CREATE SCHEMA IF NOT EXISTS catalog;
CREATE SCHEMA IF NOT EXISTS scheduler;

-- Grant the application user access to all schemas.
-- Flyway migrations in each service will create the actual tables.
GRANT ALL PRIVILEGES ON SCHEMA auth     TO movieqa;
GRANT ALL PRIVILEGES ON SCHEMA chat     TO movieqa;
GRANT ALL PRIVILEGES ON SCHEMA catalog  TO movieqa;
GRANT ALL PRIVILEGES ON SCHEMA scheduler TO movieqa;

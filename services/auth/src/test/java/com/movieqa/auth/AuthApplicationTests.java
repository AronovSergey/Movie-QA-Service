package com.movieqa.auth;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.TestPropertySource;

/**
 * Phase 0 smoke test — proves the Spring context loads without errors.
 *
 * <p>This is intentionally minimal. It answers one question: "do all beans wire together without
 * circular dependencies or missing configuration?"
 *
 * <p>LEARNING: We use H2 (in-memory) here instead of Postgres so this test runs in CI without any
 * infrastructure. Real database tests in later phases use Testcontainers with a real Postgres —
 * never mock the database for persistence tests, but mocking it for a context-load check is fine.
 *
 * <p>Flyway is disabled because there are no migrations yet (Phase 0). When we add migrations in
 * Phase 5, Flyway runs against H2 in tests, or we switch to Testcontainers for the full integration
 * test.
 */
@SpringBootTest
@TestPropertySource(
        properties = {
            "spring.datasource.url=jdbc:h2:mem:authtest;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
            "spring.datasource.driver-class-name=org.h2.Driver",
            "spring.datasource.username=sa",
            "spring.datasource.password=",
            "spring.jpa.database-platform=org.hibernate.dialect.H2Dialect",
            "spring.jpa.hibernate.ddl-auto=create-drop",
            // Clear the default_schema so H2 uses its default PUBLIC schema
            "spring.jpa.properties.hibernate.default_schema=",
            // Disable Flyway — no migrations exist yet, and H2 != Postgres dialect
            "spring.flyway.enabled=false",
            // Suppress the random-password startup log from Spring Security
            "spring.security.user.password=test"
        })
class AuthApplicationTests {

    @Test
    void contextLoads() {
        // Spring context loads successfully — proves no circular dependencies,
        // missing beans, or misconfigured components at startup.
    }
}

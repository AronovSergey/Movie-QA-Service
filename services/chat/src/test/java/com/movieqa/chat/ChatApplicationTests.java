package com.movieqa.chat;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.TestPropertySource;

/**
 * Phase 0 smoke test — proves the Spring context loads without errors.
 *
 * <p>Uses H2 in-memory DB so no running Postgres is required in CI. Flyway is disabled because no
 * migrations exist yet. WebFlux's WebClient (used for calling the RAG service) wires fine with no
 * running server — it's lazy by design.
 */
@SpringBootTest
@TestPropertySource(
        properties = {
            "spring.datasource.url=jdbc:h2:mem:chattest;DB_CLOSE_DELAY=-1;MODE=PostgreSQL",
            "spring.datasource.driver-class-name=org.h2.Driver",
            "spring.datasource.username=sa",
            "spring.datasource.password=",
            "spring.jpa.database-platform=org.hibernate.dialect.H2Dialect",
            "spring.jpa.hibernate.ddl-auto=create-drop",
            "spring.jpa.properties.hibernate.default_schema=",
            "spring.flyway.enabled=false"
        })
class ChatApplicationTests {

    @Test
    void contextLoads() {}
}

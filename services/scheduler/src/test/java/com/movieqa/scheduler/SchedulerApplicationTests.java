package com.movieqa.scheduler;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.TestPropertySource;

/**
 * Phase 0 smoke test — proves the Spring context loads without errors.
 *
 * <p>LEARNING: The scheduler depends on RabbitMQ (AMQP). We can't easily swap AMQP for an in-memory
 * alternative the way we do with H2 for Postgres. Instead, we exclude the RabbitMQ
 * auto-configuration so Spring doesn't try to open a connection during the test.
 *
 * <p>In Phase 7, the scheduler's integration tests will use Testcontainers to spin up a real
 * RabbitMQ. For this Phase 0 smoke test, we just want to confirm the bean wiring is correct — not
 * the broker connection.
 */
@SpringBootTest
@TestPropertySource(
        properties = {
            // Prevent Spring from trying to connect to RabbitMQ during the test.
            // LEARNING: spring.autoconfigure.exclude lets you remove specific
            // auto-configurations without changing the main application config.
            "spring.autoconfigure.exclude=org.springframework.boot.autoconfigure.amqp.RabbitAutoConfiguration"
        })
class SchedulerApplicationTests {

    @Test
    void contextLoads() {}
}

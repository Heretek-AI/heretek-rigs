---
name: spring-boot-virtual-thread-tuning
description: Implements Spring Boot 3.x services with Java 21 Virtual Threads and Testcontainers integration tests.
---

# Spring Boot Virtual Thread Tuning Procedure

1. Read enterprise ticket spec and inspect existing domain entities via `codebase-memory-mcp`.
2. Configure Spring Boot 3.x with Virtual Threads enabled (`spring.threads.virtual.enabled=true`).
3. Implement REST controllers, service layer, and Spring Data repositories.
4. Author comprehensive integration tests using Testcontainers (PostgreSQL / Kafka).
5. Verify zero thread-pinning issues during synchronized block execution.
6. Execute Gradle test runner: `./gradlew test --continue`.
7. Verify Jacoco code coverage exceeds 80%.

# AIDE Backend Testing Guide

This document provides a comprehensive guide to the testing strategy for the AIDE backend. All tests should adhere to these principles to ensure a robust, maintainable, and reliable codebase.

---

## 1. Core Philosophy: Integration First

Our primary goal is to test the behavior of the application as a whole. Therefore, **we prioritize integration tests over unit tests.**

-   **Integration Tests:** These tests will cover the full lifecycle of an API request, from the HTTP endpoint to the database and back. They ensure that all components (routing, dependency injection, business logic, database queries) work together correctly.
-   **Unit Tests:** These should be reserved for pure, complex, isolated business logic that is difficult or cumbersome to test through an API endpoint. An example might be a complex data transformation function with many edge cases.

If an integration test for an endpoint implicitly covers the logic of a function, we will not write a separate unit test for that function.

---

## 2. The Tech Stack

-   **Test Runner:** `pytest`
-   **HTTP Client:** `TestClient` from FastAPI, powered by `httpx`.
-   **Mocking:**
    -   `httpx`'s `HTTPXMock` for mocking external API calls (Gemini, Judge0).
    -   FastAPI's dependency injection overrides for mocking internal services (e.g., replacing a real AI service with a fake one).
-   **Containerization:** `Docker` and `Docker Compose` to create a reproducible testing environment.

---

## 3. Running Tests with Docker

All tests **must** be executed within a Docker container to ensure a consistent and isolated environment. This avoids "it works on my machine" problems.

We will create a dedicated `test` service in our `docker-compose.yml`. This service will:
-   Build from the same `Dockerfile` as the main backend.
-   Use a separate, ephemeral test database.
-   Override the entrypoint to run `pytest`.

**Example `docker-compose.test.yml` (or similar service):**
```yaml
services:
  backend-tests:
    build:
      context: ./backend
    environment:
      - DATABASE_URL=postgresql://testuser:testpass@test-db:5432/testdb
      # Add other test-specific env vars
    command: ["pytest"]
    depends_on:
      - test-db

  test-db:
    image: postgres:15
    environment:
      - POSTGRES_USER=testuser
      - POSTGRES_PASSWORD=testpass
      - POSTGRES_DB=testdb
```

To run tests, you will use: `docker compose run --rm backend-tests`

---

## 4. Database Management

-   **Isolation:** The test suite will connect to a **separate database** used exclusively for testing. The connection details will be provided via environment variables.
-   **State Management:** To ensure tests are independent, each test function will run within a **database transaction that is automatically rolled back**. This means any data created by a test is erased after the test completes, providing a clean slate for the next one. This will be managed by a `pytest` fixture.

---

## 5. Mocking and Dependencies

-   **External Services (e.g., Gemini, Judge0):** All external HTTP services **must be mocked** at the network layer using `httpx`. This makes our tests faster, more reliable, and independent of external factors. We will create fixtures that provide a mocked `httpx` client.

-   **Internal Services (e.g., AIProvider):** We will use FastAPI's dependency injection system to its full potential. For tests, we can override a high-level dependency (like an `AIProvider` class) with a fake implementation that returns predictable data, without needing to mock the underlying HTTP calls.

---

## 6. Configuration

-   **Pydantic Settings:** We will use a `Settings` object that loads from environment variables. For the test environment, we will provide a specific set of environment variables through `docker-compose` to configure the application for testing (e.g., pointing to the test database).

---

## 7. `pytest` Best Practices

-   **Fixtures:** We will extensively use fixtures to manage setup and teardown logic. Common fixtures will include:
    -   `client()`: Provides an instance of `TestClient`.
    -   `db_session()`: Provides a clean database session for each test.
    -   `httpx_mock()`: Provides a mock for `httpx` to intercept outgoing requests.
-   **File Structure:** The `backend/tests/` directory will mirror the `backend/app/` structure. For example, tests for `app/routes/v1/workspaces.py` will be in `tests/routes/v1/test_workspaces.py`.
-   **Assertions:** Assertions should be clear and informative.

---

## 8. Continuous Integration (CI)

The test suite will be the cornerstone of our CI pipeline. Every pull request will automatically trigger the test suite within a clean Docker environment. A pull request cannot be merged unless all tests pass.

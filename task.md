# AIDE Backend Implementation Plan

This document outlines the development tasks for the AIDE backend. We will follow an iterative process: you will implement a task, and I will review the solution and then write the corresponding tests to verify its functionality.

---

## Part 1: Core Project Setup

### Task 1.1: Setup FastAPI Application
- **Goal:** Create the basic FastAPI application structure.
- **File:** `app/main.py`
- **Acceptance Criteria:**
    - Initialize a `FastAPI` instance.
    - Create a root endpoint `GET /` that returns `{"message": "AIDE Backend is running"}`.
    - Create a health check endpoint `GET /health` that returns `{"status": "ok"}`.

### Task 1.2: Add Dockerfile
- **Goal:** Containerize the backend application.
- **File:** `Dockerfile` (in the `backend` directory)
- **Acceptance Criteria:**
    - Create a `Dockerfile` for the Python backend.
    - It should install dependencies from `pyproject.toml`.
    - It should run the application using an ASGI server like `uvicorn`.

### Task 1.3: Configure Docker Compose
- **Goal:** Define the multi-container setup for the entire project.
- **File:** `docker-compose.yml` (in the project root)
- **Acceptance Criteria:**
    - Create a `docker-compose.yml` file based on the "Quick Reference" section in `convo.md`.
    - For now, it only needs to define the `backend` service. We will add `supabase`, `judge0`, etc., later.

### Task 1.4: Setup Pydantic Settings
- **Goal:** Manage configuration and environment variables.
- **File:** `app/config.py`
- **Acceptance Criteria:**
    - Create a `Settings` class using `pydantic_settings.BaseSettings`.
    - Define initial settings like `PROJECT_NAME: str = "AIDE"`. We will add database URLs, API keys, etc., as we need them.

---

## Part 2: Database and Workspace API

### Task 2.1: Database Models
- **Goal:** Define the SQLAlchemy or Pydantic models for our database tables.
- **Files:** `app/models/workspace.py`, `app/models/source.py`, etc.
- **Acceptance Criteria:**
    - Create Pydantic models representing the schemas defined in `convo.md` for `workspaces`, `sources`, `labs`, `chat_messages`, and `edges`.

### Task 2.2: Database Connection
- **Goal:** Establish a connection to the Supabase (PostgreSQL) database.
- **File:** `app/services/db.py`
- **Acceptance Criteria:**
    - Create a service to manage the database connection.
    - Add the `DATABASE_URL` to the `Settings` in `app/config.py`.

### Task 2.3: Workspace API Endpoints
- **Goal:** Implement the CRUD API for workspaces.
- **File:** `app/routes/v1/workspaces.py`
- **Acceptance Criteria:**
    - Implement `POST /v1/workspaces` to create a new workspace.
    - Implement `GET /v1/workspaces/{id}` to retrieve a workspace.
    - Ensure the endpoints use the database service and Pydantic models.

---

## Our Testing Strategy

All tests will be written by the AI assistant after you complete an implementation task. The tests will rigorously follow the principles and practices outlined in our official testing document.

**Please refer to the [TESTING_GUIDE.md](TESTING_GUIDE.md) for a complete overview of our testing philosophy, tools, and procedures.**

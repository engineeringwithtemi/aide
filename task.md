# AIDE Backend Implementation Plan

This document outlines the complete development tasks for the AIDE backend MVP. Tasks will be implemented iteratively, with each task being reviewed and tested before marking as complete.

**Status Legend:**
- ⏳ **TODO** - Not started
- 🚧 **IN PROGRESS** - Currently being implemented
- ✅ **DONE** - Implemented, reviewed, and tested

---

## Progress Overview

**Last Updated:** December 25, 2025

| Phase | Status | Progress |
|-------|--------|----------|
| Part 1: Core Infrastructure | ✅ Complete | 5/5 tasks |
| Part 2: Abstract Architecture | ✅ Complete | 3/3 tasks |
| Part 3: Database Layer | ✅ Complete | 4/4 tasks |
| Part 4: External Services | 🚧 Partial | 1/3 tasks |
| Part 5: Source Implementation | ✅ Complete | 3/3 tasks |
| Part 6: Lab Implementation | ⏳ Not Started | 0/4 tasks |
| Part 7: Chat System | ⏳ Not Started | 0/4 tasks |
| Part 8: Canvas & Workspace | ⏳ Not Started | 0/2 tasks |
| Part 9: Integration & Infrastructure | 🚧 Partial | 1/4 tasks |
| Part 10: Testing & Documentation | 🚧 Partial | 1/6 tasks |

**Overall Progress:** 18/38 tasks complete (47%)

---

## Critical Path to MVP

The following tasks block the core user flow (upload PDF → generate lab → run tests):

```
┌─────────────────────────────────────────────────────────────────┐
│  ✅ PDF Upload & Parsing (Done)                                  │
│       ↓                                                          │
│  ⏳ Task 4.1: AI Provider (Gemini) ← BLOCKING                    │
│       ↓                                                          │
│  ⏳ Task 2.2: Complete Abstract Lab Class                        │
│       ↓                                                          │
│  ⏳ Task 6.1: Code Lab Implementation                            │
│       ↓                                                          │
│  ⏳ Task 6.2: Lab Generation Service                             │
│       ↓                                                          │
│  ⏳ Task 6.3: Lab API Endpoints                                  │
│       ↓                                                          │
│  ⏳ Task 4.2: Judge0 Service                                     │
│       ↓                                                          │
│  ⏳ Task 6.4: Test Result Parsing                                │
│       ↓                                                          │
│  ✅ MVP Complete - Full user journey functional                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Part 1: Core Infrastructure

### Task 1.1: Setup FastAPI Application ✅
- **Goal:** Create the complete FastAPI application with middleware, error handling, and router registration.
- **File:** `app/main.py`
- **Status:** ✅ DONE
- **Implementation:** FastAPI with CORS, request logging middleware, lifespan context, health check, exception handlers

---

### Task 1.2: Configure Pydantic Settings ✅
- **Goal:** Centralized configuration management with environment variables.
- **File:** `app/config/settings.py`
- **Status:** ✅ DONE
- **Implementation:** All env vars configured (gemini_api_key, database_url, judge0_url, supabase credentials, logging)

---

### Task 1.3: Add Core Dependencies ✅
- **Goal:** Install all required Python packages for MVP.
- **File:** `backend/pyproject.toml`
- **Status:** ✅ DONE
- **Implementation:** pymupdf, httpx, sqlalchemy, asyncpg, alembic, python-multipart, structlog, etc.

---

### Task 1.4: Create Dockerfile ✅
- **Goal:** Multi-stage Dockerfile for development, test, and production.
- **File:** `backend/Dockerfile`
- **Status:** ✅ DONE
- **Implementation:** Multi-stage build with Python 3.13, uv package manager

---

### Task 1.5: Configure Docker Compose - Backend Only ✅
- **Goal:** Docker Compose with backend and PostgreSQL for development.
- **File:** `docker-compose.yml`
- **Status:** ✅ DONE
- **Implementation:** backend, postgres, postgres-test services with health checks

---

## Part 2: Abstract Architecture (CRITICAL FOUNDATION)

### Task 2.1: Implement Abstract Source Class ✅
- **Goal:** Define the base contract for all source types with automatic caching.
- **File:** `app/sources/base.py`
- **Status:** ✅ DONE
- **Implementation:** Full abstract class with caching logic, all required methods implemented

---

### Task 2.2: Implement Abstract Lab Class 🚧
- **Goal:** Define the base contract for all lab types with validation framework.
- **File:** `app/labs/base.py`
- **Status:** 🚧 PARTIAL - Needs expansion
- **What's Done:** Basic structure with `lab_type`, `supported_sources`, `get_action_metadata()`
- **What's Missing:**
  - `get_generation_prompt(content, config)` - class method
  - `get_output_schema()` - class method
  - `validate_generation(generated)` - class method with default schema validation
  - `initialize(generated_data)` - instance method
  - `get_state()` - instance method
  - `update_state(new_state)` - instance method
  - `is_complete()` - instance method
  - `get_chat_context()` - instance method
  - `get_view_data()` - instance method
  - `get_actions()` - instance method

**Reference:** spec.md lines 407-482

---

### Task 2.3: Implement Registry System ✅
- **Goal:** Central registry for discovering source and lab types.
- **File:** `app/registry.py`
- **Status:** ✅ DONE
- **Implementation:** Full registry with decorators, get/list functions, auto-discovery

---

## Part 3: Database Layer

### Task 3.1: Create Database Schema ✅
- **Goal:** Define all database tables using Alembic migrations.
- **File:** `app/db/tables.py`
- **Status:** ✅ DONE
- **Implementation:** 6 tables (workspaces, sources, labs, chat_messages, workspace_settings, edges)

---

### Task 3.2: Implement Database Service ✅
- **Goal:** Complete CRUD operations for all tables with connection management.
- **File:** `app/db/repositories.py`
- **Status:** ✅ DONE
- **Implementation:** BaseRepository + WorkspaceRepository + SourceRepository + LabRepository

---

### Task 3.3: Create Pydantic Models ✅
- **Goal:** Request and response models for all API endpoints.
- **File:** `app/config/schemas.py`
- **Status:** ✅ DONE
- **Implementation:** All models for workspaces, sources, labs, chat, edges

---

### Task 3.4: Implement Workspace CRUD API ✅
- **Goal:** Complete CRUD API for workspaces.
- **File:** `app/routes/v1/workspaces.py`
- **Status:** ✅ DONE
- **Implementation:** POST, GET (list/single), PATCH, DELETE with cascade

---

## Part 4: External Services (CRITICAL DEPENDENCIES)

### Task 4.1: Implement AI Provider (Gemini) ⏳
- **Goal:** Gemini integration with prompt caching and structured output.
- **File:** `app/services/ai.py`
- **Status:** ⏳ TODO - **BLOCKING MVP**
- **Current State:** Only has exception wrapper decorator, no actual implementation
- **Acceptance Criteria:**
    - Abstract `AIProvider` class:
      - `supports_caching() -> bool`
      - `create_cache(content: str) -> Optional[CacheResult]`
      - `generate(prompt: str, schema: Dict, cache_id: Optional[str]) -> Dict`
    - Concrete `GeminiProvider`:
      - Initializes with `settings.gemini_api_key`
      - Creates cache with 24hr TTL
      - Generates structured output matching schema
      - Uses cached content if cache_id provided
      - Returns `CacheResult(cache_id, expires_at)`
    - `CacheResult` dataclass
    - Error handling (rate limits, invalid key, timeouts)
    - Singleton instance: `ai_provider = GeminiProvider()`

**Reference:** spec.md lines 652-719

---

### Task 4.2: Implement Judge0 Service ⏳
- **Goal:** Code execution service with test result parsing.
- **File:** `app/services/judge0.py`
- **Status:** ⏳ TODO - File exists but is empty
- **Acceptance Criteria:**
    - `Judge0Service` class with methods:
      - `execute_code(code: str, test_code: str, language: str, timeout: int) -> ExecutionResult`
      - `get_language_id(language: str) -> int` (Python=71, JavaScript=63, etc.)
    - `ExecutionResult` dataclass: `stdout`, `stderr`, `status`, `tests`
    - `TestResult` dataclass: `name`, `passed`, `error`
    - Test result parsing (unittest/pytest output)
    - Safety limits (30s timeout, 512MB memory)
    - Error handling (API errors, timeouts)

**Reference:** spec.md lines 730-821

---

### Task 4.3: Implement Storage Service (Supabase) ✅
- **Goal:** File storage for PDF uploads.
- **File:** `app/services/supabase.py`
- **Status:** ✅ DONE
- **Implementation:** upload_file, delete_files, bucket management

---

## Part 5: Source Implementation

### Task 5.1: Implement PDF Source Class ✅
- **Goal:** Concrete PDF source with parsing and caching.
- **File:** `app/sources/pdf.py`
- **Status:** ✅ DONE
- **Implementation:** Full PDFSource with all abstract methods, chapter handling, view data

---

### Task 5.2: Implement PDF Parsing Logic ✅
- **Goal:** Extract chapters and text from PDF files.
- **File:** `app/services/pdf_parser.py`
- **Status:** ✅ DONE (with minor TODO)
- **Implementation:** TOC extraction, pattern matching, page range fallback
- **Minor TODO:** `_extract_from_headings()` (font analysis) not implemented

---

### Task 5.3: Implement Source API Endpoints ✅
- **Goal:** Complete API for source management.
- **File:** `app/routes/v1/sources.py`
- **Status:** ✅ DONE
- **Implementation:** POST create, POST upload, GET, PATCH, DELETE

---

## Part 6: Lab Implementation

### Task 6.1: Implement Code Lab Class ⏳
- **Goal:** Concrete code lab for Python exercises.
- **File:** `app/labs/code_lab.py`
- **Status:** ⏳ TODO - File exists but is empty
- **Dependencies:** Task 2.2 (Abstract Lab), Task 4.1 (AI), Task 4.2 (Judge0)
- **Acceptance Criteria:**
    - `@register_lab` decorator
    - `CodeLab` class extends `Lab`:
      - `lab_type = "code_lab"`
      - Fields: `language`, `instructions`, `task_code`, `test_code`, `ai_solution`, `user_code`, `test_results`
    - Implements all abstract methods from Task 2.2
    - `TestResult` dataclass: `name`, `passed`, `error`
    - Error handling for validation failures

**Reference:** spec.md lines 484-573

---

### Task 6.2: Implement Lab Generation Logic ⏳
- **Goal:** Orchestrate AI generation with validation and retry.
- **File:** `app/services/lab_generation.py` (new file)
- **Status:** ⏳ TODO
- **Dependencies:** Task 6.1, Task 4.1, Task 4.2
- **Acceptance Criteria:**
    - `generate_lab(source: Source, lab_type: str, config: dict) -> Lab`
    - Gets content from source, builds prompt, calls AI
    - Validates via Judge0, retries up to 3 times
    - Exponential backoff on retry
    - Returns initialized lab

**Reference:** spec.md lines 806-821

---

### Task 6.3: Implement Lab API Endpoints ⏳
- **Goal:** Complete API for lab management.
- **File:** `app/routes/v1/labs.py` (new file)
- **Status:** ⏳ TODO
- **Dependencies:** Task 6.2, Task 3.2
- **Acceptance Criteria:**
    - `POST /v1/labs/generate` - Generate new lab
    - `GET /v1/labs/{lab_id}` - Get lab view data
    - `PATCH /v1/labs/{lab_id}` - Update lab state (user_code)
    - `POST /v1/labs/{lab_id}/run` - Execute tests
    - `DELETE /v1/labs/{lab_id}` - Delete lab

**Reference:** spec.md lines 1261-1270

---

### Task 6.4: Implement Test Execution & Result Parsing ⏳
- **Goal:** Parse test framework output into structured results.
- **File:** `app/services/test_parser.py` (new file)
- **Status:** ⏳ TODO
- **Dependencies:** Task 4.2
- **Acceptance Criteria:**
    - `parse_test_output(stdout, stderr, framework) -> list[TestResult]`
    - Supports Python unittest and pytest
    - Handles edge cases (syntax errors, timeouts, crashes)

---

## Part 7: Chat System

### Task 7.1: Implement @Mention Parser ⏳
- **Goal:** Parse and resolve @mentions to workspace items.
- **File:** `app/services/mention_parser.py` (new file)
- **Status:** ⏳ TODO

---

### Task 7.2: Implement Context Gathering (Generic) ⏳
- **Goal:** Gather context from sources and labs without type-specific logic.
- **File:** `app/services/context_manager.py` (new file)
- **Status:** ⏳ TODO

---

### Task 7.3: Implement Chat API Endpoints ⏳
- **Goal:** API for chat messages with Socratic teaching.
- **File:** `app/routes/v1/chat.py`
- **Status:** ⏳ TODO - File exists but is empty

---

### Task 7.4: Create Socratic Prompt Template ⏳
- **Goal:** System prompt for Socratic teaching style.
- **File:** `app/prompts/socratic_teaching.py` (new file)
- **Status:** ⏳ TODO

---

## Part 8: Canvas & Workspace Management

### Task 8.1: Implement Canvas API Endpoints ⏳
- **Goal:** API for node positioning and edges.
- **File:** `app/routes/v1/canvas.py` (new file)
- **Status:** ⏳ TODO

---

### Task 8.2: Complete Workspace API (with nested data) ⏳
- **Goal:** Enhance workspace GET to include sources, labs, edges.
- **File:** `app/routes/v1/workspaces.py`
- **Status:** ⏳ TODO - Current GET returns basic info only

---

## Part 9: Integration & Infrastructure

### Task 9.1: Complete Docker Compose (All Services) ⏳
- **Goal:** Production-ready Docker Compose with all external services.
- **File:** `docker-compose.yml`
- **Status:** ⏳ TODO - Missing Judge0, Redis

---

### Task 9.2: Environment Configuration Documentation ⏳
- **Goal:** Document all environment variables and setup.
- **File:** `.env.example`
- **Status:** ⏳ TODO

---

### Task 9.3: End-to-End Flow Integration ⏳
- **Goal:** Wire together complete user journey from PDF upload to test execution.
- **Status:** ⏳ TODO - Blocked by Part 6

---

### Task 9.4: Global Error Handling & Validation ✅
- **Goal:** Consistent error handling across all endpoints.
- **File:** `app/routes/v1/exceptions.py`
- **Status:** ✅ DONE
- **Implementation:** Custom exception handlers for EntityNotFound, Duplicate, DatabaseConnection, etc.

---

## Part 10: Testing & Documentation

### Task 10.1: Unit Tests for Abstract Classes ⏳
- **Status:** ⏳ TODO

---

### Task 10.2: Unit Tests for Concrete Classes ⏳
- **Status:** ⏳ TODO

---

### Task 10.3: Integration Tests for Services ⏳
- **Status:** ⏳ TODO

---

### Task 10.4: API Endpoint Tests ✅
- **Goal:** Test all API endpoints with FastAPI TestClient.
- **Files:** `tests/integration/test_workspaces.py`, `tests/integration/test_sources.py`
- **Status:** ✅ DONE (for implemented endpoints)
- **Implementation:** 31 integration tests covering workspaces and sources

---

### Task 10.5: End-to-End Tests (with Docker) ⏳
- **Status:** ⏳ TODO - Blocked by Part 6

---

### Task 10.6: Create API Documentation ⏳
- **Status:** ⏳ TODO

---

## Task Status Summary

**Total Tasks:** 38

**Status Breakdown:**
- ✅ DONE: 18 (47%)
- 🚧 PARTIAL: 1 (3%)
- ⏳ TODO: 19 (50%)

---

## Next Steps (Priority Order)

### Immediate (Blocking MVP):

1. **Task 4.1: AI Provider (Gemini)** - Required for lab generation
   - Implement `GeminiProvider` class
   - Add caching support
   - Add structured output generation

2. **Task 2.2: Complete Abstract Lab Class** - Foundation for Code Lab
   - Add missing abstract methods
   - Add validation framework

3. **Task 6.1: Code Lab Implementation** - Core MVP feature
   - Implement generation prompt
   - Implement state management
   - Implement view data

4. **Task 4.2: Judge0 Service** - Required for test execution
   - Implement code execution
   - Implement result parsing

5. **Task 6.2-6.4: Lab Generation & API** - Complete lab flow
   - Generation orchestration
   - API endpoints
   - Test result parsing

### Post-MVP:

6. **Part 7: Chat System** - Enhanced UX
7. **Part 8: Canvas API** - Frontend integration
8. **Part 9: Docker Compose** - Production readiness
9. **Part 10: Documentation** - Maintainability

---

## Architecture Notes

### What's Working Well:
- Clean separation: routes → services → repositories → database
- Registry pattern for extensible source/lab types
- Async throughout (SQLAlchemy, httpx)
- Structured logging with request correlation
- Comprehensive test coverage for implemented features

### Technical Debt:
- `_extract_from_headings()` in PDF parser not implemented
- Abstract Lab class needs expansion
- No integration tests for external services yet

---

**Last Updated:** December 25, 2025
**Maintainer:** Engineering Team

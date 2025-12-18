# AIDE Backend Implementation Plan

This document outlines the complete development tasks for the AIDE backend MVP. Tasks will be implemented iteratively, with each task being reviewed and tested before marking as complete.

**Status Legend:**
- ⏳ **TODO** - Not started
- 🚧 **IN PROGRESS** - Currently being implemented
- ✅ **DONE** - Implemented, reviewed, and tested

---

## Part 1: Core Infrastructure

### Task 1.1: Setup FastAPI Application ⏳
- **Goal:** Create the complete FastAPI application with middleware, error handling, and router registration.
- **File:** `app/main.py`
- **Dependencies:** None
- **Acceptance Criteria:**
    - FastAPI instance initialized with proper configuration
    - CORS middleware configured for frontend (localhost:3000)
    - Global exception handler for HTTPException and unexpected errors
    - Router registration for v1 API endpoints
    - Root endpoint `GET /` returns `{"message": "AIDE Backend", "version": "0.1.0"}`
    - Health endpoint `GET /health` returns `{"status": "ok", "database": "connected", "timestamp": ISO8601}`
    - Startup event logs application initialization
    - OpenAPI docs enabled at `/docs`

**Implementation Notes:**
```python
# Expected structure
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.v1 import workspaces, sources, labs, chat, canvas

app = FastAPI(title="AIDE Backend", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(workspaces.router, prefix="/v1/workspaces", tags=["workspaces"])
# ... other routers
```

---

### Task 1.2: Configure Pydantic Settings ⏳
- **Goal:** Centralized configuration management with environment variables.
- **File:** `app/config.py`
- **Dependencies:** None
- **Acceptance Criteria:**
    - `Settings` class using `pydantic_settings.BaseSettings`
    - Environment variables:
      - `PROJECT_NAME: str = "AIDE"`
      - `PROJECT_VERSION: str = "0.1.0"`
      - `ENVIRONMENT: str = "development"`  # development, test, production
      - `DEBUG: bool = False`
      - `LOG_LEVEL: str = "info"`
      - `DATABASE_URL: str` (required for production)
      - `GEMINI_API_KEY: str` (required)
      - `JUDGE0_URL: str = "http://localhost:2358"`
      - `SUPABASE_URL: str` (required for production)
      - `SUPABASE_KEY: str` (required for production)
    - `.env` file loaded automatically
    - Validation for required fields
    - Settings instance exported: `settings = Settings()`

---

### Task 1.3: Add Core Dependencies ⏳
- **Goal:** Install all required Python packages for MVP.
- **File:** `backend/pyproject.toml`
- **Dependencies:** None
- **Acceptance Criteria:**
    - Add to `dependencies`:
      - `pymupdf>=1.23.0` (PDF parsing)
      - `google-generativeai>=0.3.0` (Gemini AI)
      - `httpx>=0.25.0` (HTTP client for Judge0)
      - `python-multipart>=0.0.6` (file uploads)
      - `aiofiles>=23.2.0` (async file I/O)
      - `sqlalchemy[asyncio]>=2.0.0` (ORM)
      - `asyncpg>=0.29.0` (PostgreSQL driver)
      - `alembic>=1.12.0` (migrations)
    - Run `uv sync` successfully
    - All imports work without errors

---

### Task 1.4: Create Dockerfile ⏳
- **Goal:** Multi-stage Dockerfile for development, test, and production.
- **File:** `backend/Dockerfile`
- **Dependencies:** Task 1.3
- **Acceptance Criteria:**
    - Three build stages: `base`, `development`, `test`, `production`
    - Uses Python 3.13-slim
    - Installs uv package manager
    - Development stage:
      - Installs dev dependencies
      - Mounts source code as volume
      - Hot reload enabled
    - Test stage:
      - Installs dev dependencies
      - Runs pytest
    - Production stage:
      - Production dependencies only
      - Non-root user
      - Health check configured
    - Image builds successfully
    - See `docker-compose.yml` for reference

---

### Task 1.5: Configure Docker Compose - Backend Only ⏳
- **Goal:** Docker Compose with backend and PostgreSQL for development.
- **File:** `docker-compose.yml` (project root)
- **Dependencies:** Task 1.4
- **Acceptance Criteria:**
    - Services: `backend`, `postgres`
    - Backend service:
      - Builds from `backend/Dockerfile`
      - Port 8000 exposed
      - Environment variables from `.env`
      - Depends on postgres
      - Health check configured
    - Postgres service:
      - PostgreSQL 16-alpine
      - Port 5432 exposed
      - Credentials: `aide/aide/aide`
      - Volume for persistence
      - Health check configured
    - `docker compose up` starts both services
    - Backend can connect to database

**Note:** Judge0, Redis, and test database will be added in Part 9.

---

## Part 2: Abstract Architecture (CRITICAL FOUNDATION)

### Task 2.1: Implement Abstract Source Class ⏳
- **Goal:** Define the base contract for all source types with automatic caching.
- **File:** `app/sources/base.py`
- **Dependencies:** Task 1.2 (Settings)
- **Acceptance Criteria:**
    - Abstract `Source` class with all methods from convo.md Section 4.1:
      - Abstract: `source_type`, `setup()`, `get_full_content()`, `get_content_for_generation()`, `get_current_context()`, `get_available_lab_types()`, `get_chat_context()`, `get_view_data()`
      - Concrete: `get_cache_id()`, `_is_cache_valid()`, `_create_cache()`, `invalidate_cache()`
    - Automatic caching logic:
      - Checks cache validity before generation
      - Creates new cache if expired
      - Stores cache_id and expiry in database
      - Falls back if AI provider doesn't support caching
    - Type hints for all methods
    - Docstrings following Google style
    - Source registry decorator: `@register_source`
    - Registry dict: `source_registry: Dict[str, Type[Source]]`

**Reference:** convo.md lines 214-350

---

### Task 2.2: Implement Abstract Lab Class ⏳
- **Goal:** Define the base contract for all lab types with validation framework.
- **File:** `app/labs/base.py`
- **Dependencies:** Task 1.2 (Settings)
- **Acceptance Criteria:**
    - Abstract `Lab` class with all methods from convo.md Section 4.3:
      - Class methods: `lab_type`, `get_generation_prompt()`, `get_output_schema()`, `validate_generation()`
      - Instance methods: `initialize()`, `get_state()`, `update_state()`, `is_complete()`, `get_chat_context()`, `get_view_data()`, `get_actions()`
    - Validation framework:
      - Default `validate_generation()` checks schema
      - Subclasses override for custom validation (e.g., run tests via Judge0)
    - Type hints for all methods
    - Docstrings following Google style
    - Lab registry decorator: `@register_lab`
    - Registry dict: `lab_registry: Dict[str, Type[Lab]]`

**Reference:** convo.md lines 407-482

---

### Task 2.3: Implement Registry System ⏳
- **Goal:** Central registry for discovering source and lab types.
- **File:** `app/registry.py`
- **Dependencies:** Task 2.1, Task 2.2
- **Acceptance Criteria:**
    - Functions to get registered types:
      - `get_source_class(source_type: str) -> Type[Source]`
      - `get_lab_class(lab_type: str) -> Type[Lab]`
      - `list_source_types() -> list[str]`
      - `list_lab_types() -> list[str]`
    - Raises error if type not found
    - Used by API endpoints to instantiate correct classes

**Reference:** convo.md lines 575-609

---

## Part 3: Database Layer

### Task 3.1: Create Database Schema ⏳
- **Goal:** Define all database tables using Alembic migrations.
- **Files:**
  - `app/db/base.py` (SQLAlchemy models)
  - `alembic/versions/001_initial_schema.py` (migration)
- **Dependencies:** Task 1.3
- **Acceptance Criteria:**
    - SQLAlchemy declarative base
    - 5 tables matching convo.md Section 11:
      1. `workspaces` - id, name, created_at, updated_at
      2. `sources` - id, workspace_id, type, title, storage_path, metadata (JSONB), cache_id, cache_expires_at, canvas_position (JSONB), created_at, updated_at
      3. `labs` - id, workspace_id, source_id, type, config (JSONB), generated_content (JSONB), user_state (JSONB), status, canvas_position (JSONB), created_at, updated_at
      4. `chat_messages` - id, workspace_id, role, content, mentions (JSONB), created_at
      5. `edges` - id, workspace_id, source_node_id, target_node_id, created_at
    - Foreign keys with CASCADE delete
    - Indexes on frequently queried fields (workspace_id, source_id)
    - Alembic migration applies successfully
    - Tables created with correct constraints

**Reference:** convo.md lines 1174-1235

---

### Task 3.2: Implement Database Service ⏳
- **Goal:** Complete CRUD operations for all tables with connection management.
- **File:** `app/services/db.py`
- **Dependencies:** Task 3.1
- **Acceptance Criteria:**
    - Async database connection using SQLAlchemy + asyncpg
    - Connection pool configured
    - Transaction support
    - CRUD operations for all tables:
      - **Workspaces:** create, get, list, delete
      - **Sources:** create, get, update, delete, get_by_workspace
      - **Labs:** create, get, update, delete, get_by_workspace
      - **Chat Messages:** create, get_history_by_workspace
      - **Edges:** create, delete, get_by_workspace
    - Error handling for:
      - Connection failures
      - Constraint violations
      - Not found errors
    - Logging for database operations
    - Used by all API endpoints (not direct database access in routes)

---

### Task 3.3: Create Pydantic Models ⏳
- **Goal:** Request and response models for all API endpoints.
- **Files:** `app/models/*.py`
- **Dependencies:** Task 3.1
- **Acceptance Criteria:**
    - **Workspace models:**
      - `WorkspaceCreate`, `WorkspaceResponse`, `WorkspaceList`
    - **Source models:**
      - `SourceCreate`, `SourceResponse`, `SourceUploadRequest`, `SourceUpdateRequest`
    - **Lab models:**
      - `LabGenerateRequest`, `LabResponse`, `LabUpdateRequest`, `LabRunRequest`, `LabRunResponse`
    - **Chat models:**
      - `ChatMessageCreate`, `ChatMessageResponse`, `ChatHistoryResponse`
    - **Canvas models:**
      - `CanvasPositionUpdate`, `EdgeCreate`, `EdgeResponse`
    - All models have:
      - Type hints for all fields
      - Validation rules (min/max length, regex, etc.)
      - Examples in `model_config`
      - Docstrings
    - Models match database schema

---

### Task 3.4: Implement Workspace CRUD API ⏳
- **Goal:** Complete CRUD API for workspaces.
- **File:** `app/routes/v1/workspaces.py`
- **Dependencies:** Task 3.2, Task 3.3
- **Acceptance Criteria:**
    - `POST /v1/workspaces` - Create workspace
      - Body: `WorkspaceCreate`
      - Returns: `WorkspaceResponse`
      - Status: 201
    - `GET /v1/workspaces` - List all workspaces
      - Returns: `WorkspaceList`
      - Status: 200
    - `GET /v1/workspaces/{workspace_id}` - Get workspace with sources, labs, edges
      - Returns: `WorkspaceResponse` with nested data
      - Status: 200
      - Error: 404 if not found
    - `DELETE /v1/workspaces/{workspace_id}` - Delete workspace (CASCADE)
      - Status: 204
      - Error: 404 if not found
    - Uses `db` service, not direct database access
    - Error handling with proper status codes
    - OpenAPI documentation

---

## Part 4: External Services (CRITICAL DEPENDENCIES)

### Task 4.1: Implement AI Provider (Gemini) ⏳
- **Goal:** Gemini integration with prompt caching and structured output.
- **File:** `app/services/ai.py`
- **Dependencies:** Task 1.2, Task 1.3
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
    - Error handling:
      - API errors (rate limits, invalid key)
      - Network timeouts
      - Invalid schema/response
    - Logging for debugging
    - Singleton instance: `ai_provider = GeminiProvider()`

**Reference:** convo.md lines 652-719

---

### Task 4.2: Implement Judge0 Service ⏳
- **Goal:** Code execution service with test result parsing.
- **File:** `app/services/judge0.py`
- **Dependencies:** Task 1.2, Task 1.3
- **Acceptance Criteria:**
    - `Judge0Service` class with methods:
      - `execute_code(code: str, test_code: str, language: str, timeout: int) -> ExecutionResult`
      - `get_language_id(language: str) -> int` (Python=71, JavaScript=63, etc.)
    - `ExecutionResult` dataclass:
      - `stdout: str`
      - `stderr: str`
      - `status: str` ("Accepted", "Runtime Error", etc.)
      - `tests: list[TestResult]`
    - `TestResult` dataclass:
      - `name: str`
      - `passed: bool`
      - `error: Optional[str]`
    - Test result parsing:
      - Parses unittest/pytest output
      - Extracts individual test pass/fail
      - Handles edge cases (compilation errors, timeouts)
    - Safety limits:
      - Max execution time: 30s
      - Memory limit: 512MB
      - No network access (configured in Judge0)
    - Error handling:
      - Judge0 API errors
      - Timeouts
      - Invalid language
    - Singleton instance: `judge0_service = Judge0Service()`

**Reference:** convo.md lines 730-821

---

### Task 4.3: Implement Storage Service (Supabase) ⏳
- **Goal:** File storage for PDF uploads.
- **File:** `app/services/storage.py`
- **Dependencies:** Task 1.2, Task 1.3
- **Acceptance Criteria:**
    - `StorageService` class with methods:
      - `upload_file(file_content: bytes, filename: str, content_type: str) -> str` (returns URL)
      - `get_file_url(file_path: str) -> str`
      - `delete_file(file_path: str) -> None`
    - Integration with Supabase Storage:
      - Bucket: `pdfs`
      - Public access for PDFs
      - UUID-based file naming to avoid conflicts
    - Error handling:
      - Upload failures
      - Storage quota exceeded
      - Invalid file type
    - File size validation (max 50MB)
    - Content type validation (only application/pdf)
    - Singleton instance: `storage_service = StorageService()`

**Reference:** convo.md lines 179-187

---

## Part 5: Source Implementation

### Task 5.1: Implement PDF Source Class ⏳
- **Goal:** Concrete PDF source with parsing and caching.
- **File:** `app/sources/pdf.py`
- **Dependencies:** Task 2.1, Task 4.1, Task 4.3
- **Acceptance Criteria:**
    - `@register_source` decorator
    - `PDFSource` class extends `Source`:
      - `source_type = "pdf"`
      - Fields: `storage_path`, `chapters`, `current_chapter_id`
    - Implements all abstract methods:
      - `setup(config)` - Parses PDF, stores file, caches content
      - `get_full_content()` - Returns concatenated chapter text
      - `get_content_for_generation(context)` - Returns specific chapter text
      - `get_current_context()` - Returns current chapter info
      - `get_available_lab_types()` - Returns `["code_lab"]`
      - `get_chat_context()` - Returns PDF metadata for chat
      - `get_view_data()` - Returns structure for frontend
    - `Chapter` dataclass: `id`, `title`, `start_page`, `end_page`, `text`
    - Uses automatic caching from abstract class (calls `get_cache_id()`)
    - Error handling for corrupt PDFs

**Reference:** convo.md lines 352-405

---

### Task 5.2: Implement PDF Parsing Logic ⏳
- **Goal:** Extract chapters and text from PDF files.
- **File:** `app/services/pdf_parser.py`
- **Dependencies:** Task 1.3 (PyMuPDF)
- **Acceptance Criteria:**
    - `extract_chapters(file_content: bytes) -> list[Chapter]`
      - Uses PyMuPDF (fitz) to open PDF
      - Detects chapter markers:
        - Table of contents (if available)
        - Heading styles (large font, bold)
        - "Chapter N" patterns
      - Falls back to page ranges if no clear chapters
    - `extract_text(file_content: bytes) -> str`
      - Extracts all text from PDF
      - Handles multi-column layouts
      - Preserves code blocks and formatting
    - Error handling:
      - Encrypted PDFs
      - Scanned PDFs (image-only)
      - Corrupt files
    - Returns meaningful errors to user
    - Logging for debugging

**Reference:** convo.md lines 1594 (open question about parsing library)

---

### Task 5.3: Implement Source API Endpoints ⏳
- **Goal:** Complete API for source management.
- **File:** `app/routes/v1/sources.py`
- **Dependencies:** Task 5.1, Task 5.2, Task 3.2
- **Acceptance Criteria:**
    - `POST /v1/sources` - Create empty source record
      - Body: `SourceCreate` (workspace_id, type, title)
      - Returns: `SourceResponse`
      - Status: 201
    - `POST /v1/sources/{source_id}/upload` - Upload PDF
      - Body: Multipart form with file
      - Calls `source.setup()` which:
        - Parses PDF
        - Uploads to storage
        - Caches with AI provider
        - Updates database
      - Returns: `SourceResponse` with chapters
      - Status: 200
      - Error: 400 for invalid file, 413 for too large
    - `GET /v1/sources/{source_id}` - Get source view data
      - Returns: `SourceResponse` with `get_view_data()`
      - Status: 200
      - Error: 404 if not found
    - `PATCH /v1/sources/{source_id}` - Update source (e.g., current chapter)
      - Body: `SourceUpdateRequest`
      - Returns: `SourceResponse`
      - Status: 200
    - `DELETE /v1/sources/{source_id}` - Delete source
      - Deletes from storage
      - Deletes from database (CASCADE deletes labs)
      - Status: 204
    - `GET /v1/sources/{source_id}/content/{reference}` - Get chapter text
      - Returns: `{"text": "..."}`
      - Status: 200
      - Error: 404 if chapter not found
    - Uses registry to instantiate correct source class
    - Error handling with proper status codes

**Reference:** convo.md lines 1250-1259

---

## Part 6: Lab Implementation

### Task 6.1: Implement Code Lab Class ⏳
- **Goal:** Concrete code lab for Python exercises.
- **File:** `app/labs/code_lab.py`
- **Dependencies:** Task 2.2, Task 4.1, Task 4.2
- **Acceptance Criteria:**
    - `@register_lab` decorator
    - `CodeLab` class extends `Lab`:
      - `lab_type = "code_lab"`
      - Fields: `language`, `instructions`, `task_code`, `test_code`, `ai_solution`, `user_code`, `test_results`
    - Implements all abstract methods:
      - `get_generation_prompt(content, config)` - Returns prompt for Python exercise
      - `get_output_schema()` - JSON schema for AI response
      - `validate_generation(generated)` - Runs ai_solution via Judge0
      - `initialize(generated_data)` - Sets up lab from AI output
      - `get_state()` - Returns user_code, test_results
      - `update_state(new_state)` - Updates user_code
      - `is_complete()` - Returns true if all tests pass
      - `get_chat_context()` - Returns lab state for chat
      - `get_view_data()` - Returns structure for frontend (NEVER includes ai_solution)
      - `get_actions()` - Returns ["download_zip", "reset"]
    - `TestResult` dataclass: `name`, `passed`, `error`
    - Error handling for validation failures

**Reference:** convo.md lines 484-573

---

### Task 6.2: Implement Lab Generation Logic ⏳
- **Goal:** Orchestrate AI generation with validation and retry.
- **File:** `app/services/lab_generation.py`
- **Dependencies:** Task 6.1, Task 4.1, Task 4.2
- **Acceptance Criteria:**
    - `generate_lab(source: Source, lab_type: str, config: dict) -> Lab`
      - Gets lab class from registry
      - Gets content from source: `source.get_content_for_generation(config)`
      - Gets cache_id: `source.get_cache_id()`
      - Builds prompt: `lab_class.get_generation_prompt(content, config)`
      - Calls AI: `ai_provider.generate(prompt, schema, cache_id)`
      - Validates: `lab_class.validate_generation(generated)`
      - Retries up to 3 times if validation fails
      - Raises error if all attempts fail
      - Returns initialized lab
    - Retry logic:
      - Exponential backoff: 2^attempt seconds
      - Logs each attempt
      - Different prompt variations on retry
    - Error handling:
      - AI generation failures
      - Validation failures
      - Source not found
      - Invalid lab type
    - Logging for debugging generation issues

**Reference:** convo.md lines 806-821

---

### Task 6.3: Implement Lab API Endpoints ⏳
- **Goal:** Complete API for lab management.
- **File:** `app/routes/v1/labs.py`
- **Dependencies:** Task 6.2, Task 3.2
- **Acceptance Criteria:**
    - `POST /v1/labs/generate` - Generate new lab
      - Body: `LabGenerateRequest` (source_id, lab_type, chapter_id, config)
      - Calls `generate_lab()` service
      - Stores lab in database
      - Returns: `LabResponse`
      - Status: 201
      - Error: 400 for invalid request, 500 for generation failure
    - `GET /v1/labs/{lab_id}` - Get lab view data
      - Returns: `LabResponse` with `get_view_data()`
      - Status: 200
      - Error: 404 if not found
    - `PATCH /v1/labs/{lab_id}` - Update lab state
      - Body: `LabUpdateRequest` (user_code)
      - Calls `lab.update_state()`
      - Stores in database
      - Returns: `LabResponse`
      - Status: 200
    - `POST /v1/labs/{lab_id}/run` - Execute tests
      - Body: `LabRunRequest` (user_code)
      - Calls `judge0_service.execute_code(user_code, lab.test_code, lab.language)`
      - Updates `lab.test_results`
      - Updates `lab.status` to "completed" if all pass
      - Stores in database
      - Returns: `LabRunResponse` with test results
      - Status: 200
      - Error: 404 if not found, 500 for execution failure
    - `DELETE /v1/labs/{lab_id}` - Delete lab
      - Status: 204
    - Uses registry to instantiate correct lab class
    - Error handling with proper status codes

**Reference:** convo.md lines 1261-1270

---

### Task 6.4: Implement Test Execution & Result Parsing ⏳
- **Goal:** Parse test framework output into structured results.
- **File:** `app/services/test_parser.py`
- **Dependencies:** Task 4.2
- **Acceptance Criteria:**
    - `parse_test_output(stdout: str, stderr: str, framework: str) -> list[TestResult]`
      - Supports:
        - Python unittest
        - Python pytest
        - JavaScript jest (future)
      - Parses output to extract:
        - Test names
        - Pass/fail status
        - Error messages
      - Handles edge cases:
        - Syntax errors (no tests run)
        - Timeouts
        - Crashes (segfault, etc.)
        - Empty output
    - Returns empty list if no tests found
    - Returns meaningful error in TestResult if parsing fails
    - Regex patterns for each framework
    - Unit tests with real test output samples

**Reference:** convo.md lines 1602 (open question about parsing)

---

## Part 7: Chat System

### Task 7.1: Implement @Mention Parser ⏳
- **Goal:** Parse and resolve @mentions to workspace items.
- **File:** `app/services/mention_parser.py`
- **Dependencies:** None
- **Acceptance Criteria:**
    - `parse_mentions(message: str) -> list[str]`
      - Extracts @mentions from text
      - Supports:
        - `@source` (most recent source)
        - `@lab` (most recent lab)
        - `@code_lab` (most recent code lab)
        - `@pdf` (most recent PDF source)
        - `@source_<id>` (specific source by ID)
        - `@lab_<id>` (specific lab by ID)
      - Returns list of mention identifiers
    - `resolve_mentions(mentions: list[str], workspace_id: str) -> list[dict]`
      - Resolves identifiers to actual items
      - Gets items from database
      - Returns list of contexts from `get_chat_context()`
      - Handles not found gracefully (skips invalid mentions)
    - Case-insensitive matching
    - Error handling for malformed mentions

**Reference:** convo.md lines 845-894

---

### Task 7.2: Implement Context Gathering (Generic) ⏳
- **Goal:** Gather context from sources and labs without type-specific logic.
- **File:** `app/services/context_manager.py`
- **Dependencies:** Task 7.1, Task 2.1, Task 2.2
- **Acceptance Criteria:**
    - `gather_contexts(workspace_id: str, mentions: list[str]) -> list[dict]`
      - Uses registry to get source/lab classes
      - Calls `get_chat_context()` generically
      - No type-checking (no if source.type == "pdf")
      - Returns list of context dicts
    - Context structure:
      - Source: `{id, type, title, cache_id, context}`
      - Lab: `{id, type, source_id, state}`
    - Handles items not found gracefully
    - Logs context gathering for debugging

**Reference:** convo.md lines 895-924

---

### Task 7.3: Implement Chat API Endpoints ⏳
- **Goal:** API for chat messages with Socratic teaching.
- **File:** `app/routes/v1/chat.py`
- **Dependencies:** Task 7.2, Task 4.1, Task 3.2
- **Acceptance Criteria:**
    - `POST /v1/chat` - Send message, get response
      - Body: `ChatMessageCreate` (workspace_id, content)
      - Parses @mentions from content
      - Gathers contexts
      - Builds prompt with Socratic teaching instructions
      - Calls AI provider with contexts
      - Stores user message and assistant response
      - Returns: `ChatMessageResponse`
      - Status: 200
    - `GET /v1/chat/history/{workspace_id}` - Get chat history
      - Returns: `ChatHistoryResponse` (list of messages)
      - Status: 200
      - Pagination support (limit, offset)
    - Uses `SOCRATIC_TEACHING_PROMPT` template
    - Error handling with proper status codes

**Reference:** convo.md lines 1272-1277

---

### Task 7.4: Create Socratic Prompt Template ⏳
- **Goal:** System prompt for Socratic teaching style.
- **File:** `app/prompts/socratic_teaching.py`
- **Dependencies:** None
- **Acceptance Criteria:**
    - `SOCRATIC_TEACHING_PROMPT: str`
      - Instructs AI to:
        - Guide, don't solve
        - Ask leading questions
        - Point to resources (chapter, tests)
        - Encourage thinking through problems
        - Never give direct solutions
        - Use encouragement and positive reinforcement
      - Includes examples of good vs. bad responses
      - Emphasizes learning over completion
    - Used by chat endpoint

**Reference:** convo.md lines 925-948

---

## Part 8: Canvas & Workspace Management

### Task 8.1: Implement Canvas API Endpoints ⏳
- **Goal:** API for node positioning and edges.
- **File:** `app/routes/v1/canvas.py`
- **Dependencies:** Task 3.2
- **Acceptance Criteria:**
    - `PATCH /v1/canvas/positions` - Batch update node positions
      - Body: `list[CanvasPositionUpdate]` (id, type, x, y)
      - Updates canvas_position JSONB field for sources/labs
      - Returns: Success message
      - Status: 200
    - `POST /v1/canvas/edges` - Create edge between nodes
      - Body: `EdgeCreate` (workspace_id, source_node_id, target_node_id)
      - Creates edge in database
      - Returns: `EdgeResponse`
      - Status: 201
    - `DELETE /v1/canvas/edges/{edge_id}` - Delete edge
      - Status: 204
    - Validation:
      - Nodes exist
      - Nodes belong to same workspace
      - No duplicate edges
    - Error handling with proper status codes

**Reference:** convo.md lines 1279-1285

---

### Task 8.2: Complete Workspace API (with nested data) ⏳
- **Goal:** Enhance workspace GET to include sources, labs, edges.
- **File:** `app/routes/v1/workspaces.py`
- **Dependencies:** Task 3.4, Task 5.3, Task 6.3, Task 8.1
- **Acceptance Criteria:**
    - Update `GET /v1/workspaces/{workspace_id}`:
      - Returns workspace with:
        - Basic info (id, name, created_at)
        - Sources list (with get_view_data())
        - Labs list (with get_view_data())
        - Edges list
        - Canvas positions embedded
      - Single query optimization (avoid N+1)
      - Uses registry to instantiate correct source/lab classes
      - Status: 200
      - Error: 404 if not found
    - Response structure matches frontend expectations

---

## Part 9: Integration & Infrastructure

### Task 9.1: Complete Docker Compose (All Services) ⏳
- **Goal:** Production-ready Docker Compose with all external services.
- **File:** `docker-compose.yml`
- **Dependencies:** Task 1.5
- **Acceptance Criteria:**
    - Add services:
      - `postgres-test` (for test profile)
      - `judge0` (code execution)
      - `redis` (Judge0 dependency)
      - `judge0-workers` (background workers)
    - All services health checks configured
    - Networking between services configured
    - Environment variables passed correctly
    - Volumes for persistence (postgres data)
    - `docker compose up` starts all services
    - `docker compose --profile test up` includes test database
    - Services communicate correctly
    - README with setup instructions

**Reference:** convo.md lines 1633-1668

---

### Task 9.2: Environment Configuration Documentation ⏳
- **Goal:** Document all environment variables and setup.
- **File:** `.env.example` (update)
- **Dependencies:** All previous tasks
- **Acceptance Criteria:**
    - Complete `.env.example` with:
      - All required variables
      - Default values where applicable
      - Comments explaining each variable
      - Links to get API keys (Gemini)
    - Setup instructions:
      - How to get Gemini API key
      - How to configure Judge0
      - How to set up Supabase
    - Different configs for:
      - Local development
      - Docker development
      - Testing
      - Production
    - Validation script to check required vars

---

### Task 9.3: End-to-End Flow Integration ⏳
- **Goal:** Wire together complete user journey from PDF upload to test execution.
- **File:** Integration tests in `tests/integration/`
- **Dependencies:** All previous tasks
- **Acceptance Criteria:**
    - Integration test covering:
      1. Create workspace
      2. Upload PDF
      3. PDF parsed into chapters
      4. Content cached with Gemini
      5. Generate code lab from chapter
      6. Lab validated via Judge0
      7. Update user code
      8. Run tests
      9. Tests pass, lab marked complete
    - All components work together
    - Error handling at each step
    - Logging for debugging
    - Mocks for external services (AI, Judge0) in tests
    - Real services in Docker integration test

**Reference:** convo.md lines 1060-1125 (User Journey)

---

### Task 9.4: Global Error Handling & Validation ⏳
- **Goal:** Consistent error handling across all endpoints.
- **File:** `app/middleware/error_handler.py`
- **Dependencies:** Task 1.1
- **Acceptance Criteria:**
    - Global exception handlers:
      - `HTTPException` → proper status code + message
      - `ValidationError` → 422 with field errors
      - `DatabaseError` → 500 with generic message (don't expose internals)
      - `AIProviderError` → 503 with retry message
      - `Judge0Error` → 503 with retry message
      - `Exception` → 500 with generic message + error ID for logs
    - Error response format:
      ```json
      {
        "error": {
          "code": "ERROR_CODE",
          "message": "User-friendly message",
          "details": {...}  // Optional, only for validation errors
        }
      }
      ```
    - Error logging:
      - Logs full exception with traceback
      - Includes request ID for correlation
      - Structured logging (JSON format)
    - Never expose:
      - Stack traces to users
      - Database queries
      - API keys
      - Internal paths

**Reference:** convo.md lines 1596-1597 (error handling question)

---

## Part 10: Testing & Documentation

### Task 10.1: Unit Tests for Abstract Classes ⏳
- **Goal:** Test abstract class behavior and contracts.
- **Files:** `tests/unit/test_sources.py`, `tests/unit/test_labs.py`
- **Dependencies:** Task 2.1, Task 2.2
- **Acceptance Criteria:**
    - Tests for Source abstract class:
      - Cache validation logic
      - Cache creation and expiry
      - Cache invalidation
      - Mock concrete class for testing
    - Tests for Lab abstract class:
      - Validation framework
      - State management
      - Mock concrete class for testing
    - Test registry:
      - Register and retrieve source types
      - Register and retrieve lab types
      - Error for unregistered types
    - 100% coverage for abstract classes

**See TESTING_GUIDE.md for detailed testing standards.**

---

### Task 10.2: Unit Tests for Concrete Classes ⏳
- **Goal:** Test PDF Source and Code Lab implementations.
- **Files:** `tests/unit/test_pdf_source.py`, `tests/unit/test_code_lab.py`
- **Dependencies:** Task 5.1, Task 6.1
- **Acceptance Criteria:**
    - Tests for PDFSource:
      - PDF parsing
      - Chapter extraction
      - Content retrieval
      - View data format
      - Error cases (corrupt PDF)
    - Tests for CodeLab:
      - Generation prompt format
      - Output schema validation
      - State management
      - Completion logic
      - View data format (no ai_solution)
    - Mock external services (AI, storage)
    - Edge cases covered

---

### Task 10.3: Integration Tests for Services ⏳
- **Goal:** Test service interactions with mocked external APIs.
- **Files:** `tests/integration/test_services.py`
- **Dependencies:** Task 4.1, Task 4.2, Task 4.3
- **Acceptance Criteria:**
    - Tests for AI Provider:
      - Cache creation
      - Generation with cache
      - Generation without cache
      - Error handling
      - Mock Gemini API responses
    - Tests for Judge0 Service:
      - Code execution
      - Test parsing
      - Error cases (timeout, compilation error)
      - Mock Judge0 API responses
    - Tests for Storage Service:
      - File upload
      - File retrieval
      - File deletion
      - Mock Supabase Storage
    - Tests run quickly (<5s total)

---

### Task 10.4: API Endpoint Tests ⏳
- **Goal:** Test all API endpoints with FastAPI TestClient.
- **Files:** `tests/api/test_*.py`
- **Dependencies:** All route tasks
- **Acceptance Criteria:**
    - Tests for each endpoint:
      - Happy path (200, 201, 204)
      - Validation errors (400, 422)
      - Not found errors (404)
      - Server errors (500, 503)
    - Request/response validation
    - Authentication (when added)
    - Mock database and services
    - OpenAPI schema validation
    - Tests organized by route file

---

### Task 10.5: End-to-End Tests (with Docker) ⏳
- **Goal:** Full integration test with real services in Docker.
- **Files:** `tests/e2e/test_user_journey.py`
- **Dependencies:** Task 9.1, Task 9.3
- **Acceptance Criteria:**
    - Complete user journey test:
      - Uses Docker Compose with test profile
      - Real PostgreSQL database
      - Real Judge0 for code execution
      - Mocked AI provider (too expensive for CI)
      - Mocked storage (no Supabase in CI)
      - Covers all steps from convo.md Section 9
    - Setup and teardown:
      - Starts services before tests
      - Cleans database after tests
      - Stops services after tests
    - Runs in CI pipeline
    - Takes <2 minutes

---

### Task 10.6: Create API Documentation ⏳
- **Goal:** Comprehensive API documentation for frontend developers.
- **File:** `docs/API.md`
- **Dependencies:** All route tasks
- **Acceptance Criteria:**
    - Documentation for each endpoint:
      - Description
      - HTTP method and path
      - Request body schema with examples
      - Response schema with examples
      - Error codes and messages
      - Authentication (when added)
    - Organized by resource (workspaces, sources, labs, etc.)
    - Links to Pydantic model definitions
    - Postman/Insomnia collection export
    - OpenAPI spec available at `/docs`

---

## Task Status Summary

**Total Tasks:** 45

**Status Breakdown:**
- ⏳ TODO: 45 (100%)
- 🚧 IN PROGRESS: 0 (0%)
- ✅ DONE: 0 (0%)

---

## Implementation Order (Dependency Graph)

### Phase 1: Foundation (Week 1)
1. Part 1: Core Infrastructure (Tasks 1.1-1.5)
2. Part 2: Abstract Architecture (Tasks 2.1-2.3) ⚠️ CRITICAL
3. Part 3: Database Layer (Tasks 3.1-3.2)

### Phase 2: External Services (Week 2)
4. Part 4: External Services (Tasks 4.1-4.3)
5. Part 3: Database Layer (Tasks 3.3-3.4)

### Phase 3: Core Features (Weeks 3-4)
6. Part 5: Source Implementation (Tasks 5.1-5.3)
7. Part 6: Lab Implementation (Tasks 6.1-6.4)

### Phase 4: Advanced Features (Week 5)
8. Part 7: Chat System (Tasks 7.1-7.4)
9. Part 8: Canvas & Workspace (Tasks 8.1-8.2)

### Phase 5: Integration & Testing (Week 6)
10. Part 9: Integration & Infrastructure (Tasks 9.1-9.4)
11. Part 10: Testing & Documentation (Tasks 10.1-10.6)

---

## Notes

- **Review Process:** After implementing each task, code will be reviewed using [REVIEW_GUIDELINE.md](./REVIEW_GUIDELINE.md)
- **Testing Process:** Tests will be written by reviewer after implementation, following [TESTING_GUIDE.md](./TESTING_GUIDE.md)
- **Status Updates:** This file will be updated after each task is completed and reviewed
- **Architecture Reference:** See [convo.md](./convo.md) for complete specification
- **Questions:** Open questions are tracked in convo.md Section 16

---

**Last Updated:** December 18, 2025
**Maintainer:** Engineering Team

# AIDE: Complete Project Context

**Last Updated:** December 17, 2025
**Status:** Architecture finalized, ready for implementation

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Core Concepts](#2-core-concepts)
3. [Architecture Decisions](#3-architecture-decisions)
4. [Abstract Class Design](#4-abstract-class-design)
5. [Caching System](#5-caching-system)
6. [Code Execution (Judge0)](#6-code-execution-judge0)
7. [Chat System](#7-chat-system)
8. [UI Architecture (n8n Style)](#8-ui-architecture-n8n-style)
9. [User Journey](#9-user-journey)
10. [Technology Stack](#10-technology-stack)
11. [Database Schema](#11-database-schema)
12. [API Endpoints](#12-api-endpoints)
13. [Contributor Guide](#13-contributor-guide)
14. [MVP Scope](#14-mvp-scope)
15. [Prototype Specification](#15-prototype-specification)
16. [Open Questions](#16-open-questions)

---

## 1. Project Overview

### What is AIDE?

A visual workspace that transforms passive learning materials (PDFs, GitHub repos, videos) into interactive practice tools (code labs, flashcards, quizzes, terminals).

**Core Philosophy:** Learn by DOING, not just reading.

### The Problem

You read a technical book about building a web server. You understand the words, but do you _really_ understand how it works? Reading alone doesn't solidify knowledge.

### The Solution

Turn that chapter into a hands-on coding exercise where you implement a mini web server. When the tests pass, you KNOW you understood it.

### Key Characteristics

| Characteristic      | Description                              |
| ------------------- | ---------------------------------------- |
| **Open source**     | Anyone can fork, run locally, contribute |
| **Self-hosted**     | Everything runs via `docker compose up`  |
| **Local first**     | No cloud dependencies, no accounts       |
| **No monetization** | Personal project solving a real problem  |

### Target Users

Anyone who learns by doing — software engineers, students, self-learners. Initially focused on Python learners.

---

## 2. Core Concepts

### Two Primitives

The system has two types of building blocks:

#### Sources (Input)

Things you learn FROM. Read-only reference materials.

- **MVP:** PDF only
- **Later:** GitHub repos, YouTube videos, documentation sites

A source knows:

- How to display itself (PDF viewer, video player, file tree)
- Where you currently are (Chapter 5, timestamp 2:30, file `server.js`)
- What can be generated from it (code lab, flashcards, quiz)
- Its full content for AI caching

#### Labs (Output)

Things you learn WITH. Interactive tools you work in.

- **MVP:** Code Labs only (Python)
- **Later:** Flashcards, quizzes, terminal practice

A lab knows:

- What data it needs to start (starter code, tests, instructions)
- How to display itself (code editor, flashcard deck, quiz interface)
- When it's "complete" (all tests pass, all cards reviewed)
- Its current state for persistence

### The Workspace

A workspace is a container that holds:

- Sources (learning materials)
- Labs (interactive tools)
- Chat (AI assistant)
- Canvas positions (spatial layout)

Think of it as a "project" for learning a specific topic.

---

## 3. Architecture Decisions

### 3.1 Two-Server Split

```
┌─────────────────────────────────────────────────────────────┐
│                   FRONTEND (React)                           │
│                                                              │
│  Responsibilities:                                           │
│  • React Flow canvas (nodes, edges, zoom, pan)               │
│  • Modal system (full-screen views)                          │
│  • Monaco editor (code editing)                              │
│  • PDF viewer (react-pdf)                                    │
│  • Chat UI                                                   │
│  • Local UI state (which modal is open, editor content)      │
│                                                              │
│  Does NOT:                                                   │
│  • Talk to AI directly                                       │
│  • Execute code                                              │
│  • Parse PDFs                                                │
│  • Store anything permanently                                │
│  • Contain business logic                                    │
└─────────────────────────────────────────────────────────────┘
                           ↓ HTTP/REST
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI)                          │
│                                                              │
│  Responsibilities:                                           │
│  • PDF parsing (extract chapters, text)                      │
│  • AI integration (Gemini calls, prompt caching)             │
│  • Lab generation (create exercises, validate them)          │
│  • Code execution (send to Judge0, parse results)            │
│  • Workspace persistence (save/load state)                   │
│  • Chat history and context management                       │
│  • All business logic                                        │
│                                                              │
│  Talks to:                                                   │
│  • Gemini API (AI generation)                                │
│  • Judge0 (code execution)                                   │
│  • Supabase (persistence)                                    │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                   JUDGE0 (Code Execution)                    │
│                                                              │
│  • Isolated Docker containers                                │
│  • Runs user code safely                                     │
│  • Returns stdout, stderr, status                            │
│  • Resource limits (CPU, memory, time)                       │
│  • No network access                                         │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Why This Split?

**Frontend stays dumb (in a good way):**

- Only renders things and captures input
- Doesn't know what Gemini is or how to parse PDFs
- Easier to test (mock the API)
- Easier to change AI providers (frontend doesn't care)
- Easier to reason about (UI logic only)

**Backend is the brain:**

- All "smart" stuff in one place
- AI prompts and caching logic
- PDF parsing and chapter extraction
- Test validation (run AI's solution before showing to user)
- One place to debug AI issues
- API keys stay server-side (security)

### 3.3 Storage: Supabase

Using Supabase (local Docker image) which provides:

- PostgreSQL database
- File storage (for PDFs)
- No external dependencies
- Easy to self-host

### 3.4 Locked-In Decisions

These decisions are final:

1. ✅ "Labs" not "Artifacts"
2. ✅ Judge0 for code execution
3. ✅ Generic context interface
4. ✅ @mention system for chat
5. ✅ n8n-style UI (cards + modal)
6. ✅ Small cards (200x120px)
7. ✅ Full modal (1200x90vh)
8. ✅ Sidebar for adding items
9. ✅ React Flow for canvas
10. ✅ One exercise per concept
11. ✅ Backend handles all business logic
12. ✅ Frontend is just a renderer

---

## 4. Abstract Class Design

### Design Philosophy

The **backend defines the contracts** (abstract Source, abstract Lab). Contributors implement concrete classes on the backend. The **frontend is just a renderer** — it receives data from `get_view_data()` and displays it.

### 4.1 Abstract Source Class

```python
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List

class Source(ABC):
    """Base class all sources must implement"""

    id: str
    workspace_id: str
    type: str
    title: str
    cache_id: Optional[str] = None
    cache_expires_at: Optional[datetime] = None

    @property
    @abstractmethod
    def source_type(self) -> str:
        """Unique identifier for this source type (e.g., 'pdf', 'github')"""
        pass

    @abstractmethod
    async def setup(self, config: Dict[str, Any]) -> 'SourceMetadata':
        """
        Called when source is first added/configured.
        For PDF: parse chapters, cache with AI
        For GitHub: clone repo, index files
        """
        pass

    @abstractmethod
    async def get_full_content(self) -> str:
        """
        Returns ALL content for this source to be cached.
        - PDF: entire book text with chapter markers
        - GitHub: all file contents concatenated
        - Video: full transcript

        This is called by the abstract class when caching.
        Concrete classes just return the content.
        """
        pass

    @abstractmethod
    async def get_content_for_generation(self, context: Dict[str, Any]) -> str:
        """
        Extract text content for AI generation.
        Context might specify chapter_id, file_path, timestamp, etc.
        """
        pass

    @abstractmethod
    def get_current_context(self) -> Dict[str, Any]:
        """
        What is the user currently viewing?
        Returns: { reference: "Chapter 5", page: 42, ... }
        """
        pass

    @abstractmethod
    def get_available_lab_types(self) -> List[str]:
        """What labs can be generated from this source?"""
        pass

    @abstractmethod
    def get_chat_context(self) -> Dict[str, Any]:
        """What context should chat have about this source?"""
        pass

    @abstractmethod
    def get_view_data(self) -> Dict[str, Any]:
        """
        Data the frontend needs to render this source.
        Frontend doesn't decide what to show — backend tells it.
        """
        pass

    # ─────────────────────────────────────────────
    # CACHING (handled by abstract class automatically)
    # ─────────────────────────────────────────────

    async def get_cache_id(self) -> Optional[str]:
        """
        Returns valid cache_id, creating/refreshing if needed.
        Called before any AI generation.
        """
        if self._is_cache_valid():
            return self.cache_id

        return await self._create_cache()

    def _is_cache_valid(self) -> bool:
        """Check if current cache exists and hasn't expired"""
        if not self.cache_id or not self.cache_expires_at:
            return False
        return datetime.utcnow() < self.cache_expires_at

    async def _create_cache(self) -> Optional[str]:
        """Create new cache with AI provider"""
        from app.services.ai import ai_provider
        from app.services.db import db

        # Get full content from concrete class
        content = await self.get_full_content()

        # Check if provider supports caching
        if not ai_provider.supports_caching():
            return None

        # Create cache with provider (e.g., Gemini)
        cache_result = await ai_provider.create_cache(content)

        if cache_result:
            self.cache_id = cache_result.cache_id
            self.cache_expires_at = cache_result.expires_at

            # Persist to database
            await db.update_source(self.id, {
                "cache_id": self.cache_id,
                "cache_expires_at": self.cache_expires_at,
            })

        return self.cache_id

    async def invalidate_cache(self) -> None:
        """Force cache refresh on next generation"""
        from app.services.db import db

        self.cache_id = None
        self.cache_expires_at = None

        await db.update_source(self.id, {
            "cache_id": None,
            "cache_expires_at": None,
        })
```

### 4.2 Concrete PDF Source Example

```python
class PDFSource(Source):
    source_type = "pdf"

    storage_path: str
    chapters: List[Chapter]
    current_chapter_id: Optional[str] = None

    async def setup(self, config: Dict[str, Any]) -> SourceMetadata:
        file_path = config['file_path']

        # Parse PDF
        self.chapters = await pdf_parser.extract_chapters(file_path)

        # Store in Supabase
        self.storage_path = await storage.upload(file_path)

        # Cache with AI provider (abstract class handles this)
        await self.get_cache_id()

        return SourceMetadata(
            title=self.title,
            chapters=[{"id": ch.id, "title": ch.title} for ch in self.chapters],
        )

    async def get_full_content(self) -> str:
        """Return entire PDF text for caching"""
        content_parts = []
        for chapter in self.chapters:
            content_parts.append(f"=== {chapter.title} ===\n{chapter.text}")
        return "\n\n".join(content_parts)

    async def get_content_for_generation(self, context: Dict[str, Any]) -> str:
        """Return just the chapter text for this specific generation"""
        chapter_id = context.get('chapter_id')
        chapter = next(ch for ch in self.chapters if ch.id == chapter_id)
        return chapter.text

    def get_available_lab_types(self) -> List[str]:
        return ["code_lab", "flashcard_lab", "quiz_lab"]

    def get_view_data(self) -> Dict[str, Any]:
        return {
            "type": "pdf",
            "storage_url": self.storage_path,
            "chapters": [
                {"id": ch.id, "title": ch.title, "start_page": ch.start_page}
                for ch in self.chapters
            ],
            "current_chapter_id": self.current_chapter_id,
        }
```

### 4.3 Abstract Lab Class

```python
class Lab(ABC):
    """Base class all labs must implement"""

    id: str
    workspace_id: str
    source_id: str
    type: str
    status: str  # 'pending', 'in_progress', 'completed'

    @property
    @abstractmethod
    def lab_type(self) -> str:
        """Unique identifier (e.g., 'code_lab', 'flashcard_lab')"""
        pass

    @classmethod
    @abstractmethod
    def get_generation_prompt(cls, content: str, config: Dict[str, Any]) -> str:
        """
        Build the prompt to send to AI.
        Content = chapter text (from source)
        Config = user options (language, difficulty, etc.)
        """
        pass

    @classmethod
    @abstractmethod
    def get_output_schema(cls) -> Dict[str, Any]:
        """JSON schema for what AI must return"""
        pass

    @classmethod
    async def validate_generation(cls, generated: Dict[str, Any]) -> bool:
        """
        Validate AI output before giving to user.
        Default: just check schema. Override for custom validation.
        """
        return True

    @abstractmethod
    async def initialize(self, generated_data: Dict[str, Any]) -> None:
        """Set up lab with AI-generated content"""
        pass

    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """Current user state (their code, progress, etc.)"""
        pass

    @abstractmethod
    async def update_state(self, new_state: Dict[str, Any]) -> None:
        """User made changes (wrote code, flipped card, etc.)"""
        pass

    @abstractmethod
    def is_complete(self) -> bool:
        """Has user finished this lab?"""
        pass

    @abstractmethod
    def get_chat_context(self) -> Dict[str, Any]:
        """What context should chat have about this lab?"""
        pass

    @abstractmethod
    def get_view_data(self) -> Dict[str, Any]:
        """Data frontend needs to render this lab"""
        pass

    def get_actions(self) -> List[Dict[str, Any]]:
        """Available actions (download, reset, etc.)"""
        return []
```

### 4.4 Concrete Code Lab Example

```python
class CodeLab(Lab):
    lab_type = "code_lab"

    language: str
    instructions: str
    task_code: str      # Template with TODOs
    test_code: str      # Read-only tests
    ai_solution: str    # For validation, NEVER sent to frontend
    user_code: str      # User's current work
    test_results: Optional[List[TestResult]] = None

    @classmethod
    def get_generation_prompt(cls, content: str, config: Dict[str, Any]) -> str:
        language = config.get('language', 'python')
        return f"""
        You are creating a coding exercise from educational content.

        Chapter content:
        {content}

        Language: {language}

        Create ONE cohesive exercise that tests understanding of the core concepts.
        The exercise should be comprehensive - if the user can complete it, they understood the material.

        Return JSON with:
        - instructions: Clear description of what to build
        - task_code: Starter code with TODO comments
        - test_code: Comprehensive tests using unittest
        - ai_solution: Complete working solution (for validation)
        """

    @classmethod
    def get_output_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "instructions": {"type": "string"},
                "task_code": {"type": "string"},
                "test_code": {"type": "string"},
                "ai_solution": {"type": "string"},
            },
            "required": ["instructions", "task_code", "test_code", "ai_solution"]
        }

    @classmethod
    async def validate_generation(cls, generated: Dict[str, Any]) -> bool:
        """Run AI solution against tests via Judge0"""
        result = await judge0.execute(
            code=generated['ai_solution'],
            test_code=generated['test_code'],
            language='python'
        )
        return result.all_passed

    async def initialize(self, generated_data: Dict[str, Any]) -> None:
        self.instructions = generated_data['instructions']
        self.task_code = generated_data['task_code']
        self.test_code = generated_data['test_code']
        self.ai_solution = generated_data['ai_solution']
        self.user_code = generated_data['task_code']  # Start with template
        self.status = 'in_progress'

    def is_complete(self) -> bool:
        if not self.test_results:
            return False
        return all(t.passed for t in self.test_results)

    def get_view_data(self) -> Dict[str, Any]:
        # NOTE: ai_solution is NOT included - never sent to frontend
        return {
            "type": "code_lab",
            "language": self.language,
            "instructions": self.instructions,
            "task_code": self.task_code,
            "test_code": self.test_code,
            "user_code": self.user_code,
            "test_results": [t.dict() for t in self.test_results] if self.test_results else None,
            "is_complete": self.is_complete(),
        }

    def get_actions(self) -> List[Dict[str, Any]]:
        return [
            {"id": "download_zip", "label": "Download as ZIP"},
            {"id": "reset", "label": "Reset to Original"},
        ]
```

### 4.5 Backend Registry

```python
# registry.py
from typing import Dict, Type

source_registry: Dict[str, Type[Source]] = {}
lab_registry: Dict[str, Type[Lab]] = {}

def register_source(cls: Type[Source]):
    """Decorator to register a source type"""
    source_registry[cls.source_type] = cls
    return cls

def register_lab(cls: Type[Lab]):
    """Decorator to register a lab type"""
    lab_registry[cls.lab_type] = cls
    return cls

# Usage
@register_source
class PDFSource(Source):
    source_type = "pdf"
    ...

@register_lab
class CodeLab(Lab):
    lab_type = "code_lab"
    ...

@register_lab
class FlashcardLab(Lab):
    lab_type = "flashcard_lab"
    ...
```

---

## 5. Caching System

### How It Works

The abstract `Source` class handles all caching logic automatically. Concrete classes only need to implement `get_full_content()`.

### Caching Flow

```
User clicks "Generate Code Lab"
        ↓
Backend calls source.get_cache_id()
        ↓
Abstract class checks: is cache_id valid and not expired?
        ↓
    ┌───YES───┐              ┌───NO────┐
    ↓                        ↓
Return                   Call concrete class's
cache_id                 get_full_content()
                             ↓
                         Send to AI provider (Gemini)
                             ↓
                         Receive new cache_id
                             ↓
                         Store in DB with expiry timestamp
                             ↓
                         Return cache_id
        ↓
Generation continues with cache_id
```

### When Caching Happens

1. **On source setup (PDF upload):** Cache entire content with AI provider
2. **On generation request:** Check if cache is valid
3. **If expired:** Automatically recache before generation
4. **Store cache ID:** In database with expiry timestamp
5. **Fallback:** If provider doesn't support caching, send full content each time

### AI Provider Interface

```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class CacheResult:
    cache_id: str
    expires_at: datetime

class AIProvider(ABC):

    @abstractmethod
    def supports_caching(self) -> bool:
        pass

    @abstractmethod
    async def create_cache(self, content: str) -> Optional[CacheResult]:
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        schema: Dict[str, Any],
        cache_id: Optional[str] = None
    ) -> Dict[str, Any]:
        pass


class GeminiProvider(AIProvider):

    def supports_caching(self) -> bool:
        return True

    async def create_cache(self, content: str) -> Optional[CacheResult]:
        response = await gemini.caching.create(
            model="gemini-1.5-pro",
            contents=[{"role": "user", "parts": [{"text": content}]}],
            ttl="86400s"  # 24 hours
        )
        return CacheResult(
            cache_id=response.name,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )

    async def generate(
        self,
        prompt: str,
        schema: Dict[str, Any],
        cache_id: Optional[str] = None
    ) -> Dict[str, Any]:
        if cache_id:
            response = await gemini.generate_content(
                cached_content=cache_id,
                contents=[{"role": "user", "parts": [{"text": prompt}]}],
                generation_config={"response_schema": schema}
            )
        else:
            response = await gemini.generate_content(
                contents=[{"role": "user", "parts": [{"text": prompt}]}],
                generation_config={"response_schema": schema}
            )
        return response
```

### Benefits of Caching

- **97% token reduction** on subsequent calls
- **67% cost savings** with Gemini caching
- **Faster responses** (AI already has context)
- **Better output** (AI has full book context, can reference other chapters)

---

## 6. Code Execution (Judge0)

### Why Judge0?

- Battle-tested (used by HackerRank, CodeChef)
- Supports 60+ programming languages
- Safe, isolated execution in Docker containers
- Resource limits (CPU, memory, time)
- No network access
- Self-hostable

### Execution Flow

```
1. User clicks "Run Tests" in Code Lab
        ↓
2. Frontend sends: { labId, userCode }
        ↓
3. Backend retrieves lab (gets test_code)
        ↓
4. Backend combines: userCode + test_code
        ↓
5. Sends to Judge0 API:
   {
     language_id: 71,  // Python 3
     source_code: combined_code,
     stdin: ""
   }
        ↓
6. Judge0 executes in isolated container
        ↓
7. Returns:
   {
     stdout: "test_sum PASSED\ntest_product FAILED\n...",
     stderr: "AssertionError: None != 6",
     status: { id: 3, description: "Accepted" }
   }
        ↓
8. Backend parses output to extract individual test results
        ↓
9. Returns structured results:
   {
     tests: [
       { name: "test_sum", passed: true },
       { name: "test_product", passed: false, error: "Expected 6, got None" }
     ],
     stdout: "Debug: calculating sum"
   }
        ↓
10. Frontend displays in Results tab
```

### Language Support

| Language             | Judge0 ID |
| -------------------- | --------- |
| Python 3             | 71        |
| JavaScript (Node.js) | 63        |
| Rust                 | 73        |
| Go                   | 60        |
| C++                  | 54        |

### Safety & Isolation

Judge0 executes code in Docker containers with:

- No network access
- Memory limits (512MB)
- CPU limits (0.5 CPU)
- Time limits (30 seconds max)
- Isolated filesystem

### Generation Validation

Before showing a Code Lab to the user, we validate the AI-generated tests:

```python
async def generate_lab(request: GenerateLabRequest):
    # ... generate with AI ...

    # Validate: run AI's solution against the tests
    for attempt in range(3):
        if await lab_class.validate_generation(generated):
            break
        # Regenerate if validation fails
        generated = await ai_provider.generate(prompt, schema, cache_id)
    else:
        raise GenerationError("Could not generate valid exercise after 3 attempts")

    # Only return to user if validation passed
    return generated
```

---

## 7. Chat System

### Overview

An AI assistant that:

- Has context of the entire workspace
- Can be referenced with @mentions
- Uses Socratic method (guides, doesn't solve)
- Helps debug, explain, and clarify concepts

### Chat is NOT a Source or Lab

Chat is a workspace-level utility. It doesn't extend Source or Lab because:

- It doesn't generate content
- It doesn't have input/output schemas
- It's a helper, not a learning tool
- It reads from sources/labs, doesn't produce them

### @Mention System

Users can reference workspace items:

```
@source      → Current/active source
@lab         → Most recent lab
@code_lab    → Most recent code lab
@pdf         → Most recent PDF source
@source_123  → Specific source by ID
@lab_456     → Specific lab by ID
```

### How @Mentions Work

```python
class Chat:
    def __init__(self, workspace: Workspace):
        self.workspace = workspace
        self.messages: List[Message] = []

    async def send(self, message: str) -> str:
        # 1. Parse @mentions
        mentions = self._parse_mentions(message)
        # e.g., ['source', 'code_lab']

        # 2. Get contexts GENERICALLY (no type checks!)
        contexts = []
        for mention in mentions:
            # Try as type first
            items = self.workspace.get_items_by_type(mention)
            if items:
                contexts.append(items[0].get_chat_context())
                continue

            # Try as ID
            item = self.workspace.get_item_by_id(mention)
            if item:
                contexts.append(item.get_chat_context())

        # 3. Send to AI with Socratic teaching prompt
        response = await ai_provider.chat(
            system_prompt=SOCRATIC_TEACHING_PROMPT,
            contexts=contexts,
            messages=self.messages,
            new_message=message
        )

        return response
```

### Generic Context Interface

Every Source and Lab provides `get_chat_context()`:

```python
# Source
source.get_chat_context() → {
    "id": "source_123",
    "type": "pdf",
    "title": "How to Linux",
    "cache_id": "cache_abc",
    "context": {"chapter": "Chapter 5", "page": 42}
}

# Lab
lab.get_chat_context() → {
    "id": "lab_456",
    "type": "code_lab",
    "source_id": "source_123",
    "state": {"user_code": "...", "test_results": [...]}
}
```

**This means:**

- Chat doesn't need to know about specific types
- Adding new source/lab types requires NO chat changes
- Everything is generic and extensible

### Teaching Philosophy (System Prompt)

Chat uses Socratic method — it GUIDES, doesn't SOLVE:

**Bad response (typical chatbot):**

```
User: Why isn't my code working?
AI: The error is because you didn't return anything.
    Change line 5 to: return a + b
```

**Good response (learning-focused):**

```
User: Why isn't my code working?
AI: I see your calculate_sum function. Let's think through this:

    1. What should this function do with a and b?
    2. What does the test expect the function to return?
    3. What Python keyword sends a value back from a function?

    Look at the error message - what does "assert None == 5" tell you?
```

---

## 8. UI Architecture (n8n Style)

### The Pattern: Small Cards + Full Modal

```
┌────────────────────┬────────────────────────────────────┐
│     SIDEBAR        │              CANVAS                 │
│   (Add items)      │          (React Flow)               │
│                    │                                     │
│ 📖 Add PDF         │   ┌────────┐      ┌────────┐       │
│ 🔗 Add GitHub      │   │  PDF   │─────▶│ Code   │       │
│ 💻 Add Code Lab    │   │  Ch.5  │      │  Lab   │       │
│ 📇 Add Flashcards  │   └────────┘      └────────┘       │
│ 💬 Add Chat        │                                     │
│                    │   ┌────────┐                        │
│                    │   │  Chat  │                        │
│                    │   └────────┘                        │
└────────────────────┴────────────────────────────────────┘

              Double-click any node → Opens full modal
```

### Why This Pattern?

| Benefit                | Description                                |
| ---------------------- | ------------------------------------------ |
| ✅ Canvas stays clean  | Can see 10+ items at once                  |
| ✅ Spatial overview    | Small cards show relationships             |
| ✅ Full space for work | Modal provides 1200x90vh                   |
| ✅ Proven pattern      | Used by n8n, Figma, VS Code                |
| ✅ No size constraints | Reading/editing in modal, not cramped node |

### Rejected Approach: Large Resizable Nodes

| Problem                 | Impact                   |
| ----------------------- | ------------------------ |
| ❌ Takes too much space | Can only see 2-3 items   |
| ❌ Lots of scrolling    | Poor UX                  |
| ❌ Reading constrained  | Node size limits content |
| ❌ Cognitive overload   | Too much on screen       |

### Node Sizes

- Source card: 200x120px
- Lab card: 200x120px
- Chat card: 200x120px

### Modal Size

- Full modal: 1200x90vh
- Contains full PDF viewer, code editor, etc.

### Card Designs

**PDF Card (blue):**

```
┌──────────────────────┐
│ 📖 PDF               │
│ How to Linux         │
│ Chapter 5            │
└──────────────────────┘
```

**Code Lab Card (purple):**

```
┌──────────────────────┐
│ 💻 Code Lab          │
│ Functions Lab        │
│ ● In Progress        │
└──────────────────────┘
```

**Chat Card (orange):**

```
┌──────────────────────┐
│ 💬 Chat              │
│ AI Assistant         │
│ 12 messages          │
└──────────────────────┘
```

### React Flow Integration

**What React Flow provides:**

- Canvas with pan/zoom
- Node dragging
- Node connections (edges)
- Mini-map
- Controls (zoom, fit view)
- Background grid
- Multi-select
- Keyboard shortcuts

**What we build:**

- Custom small card components
- Modal system for full content view
- Sidebar for adding items
- Node data management

---

## 9. User Journey

### Complete Flow

```
CREATE WORKSPACE
1. User clicks "Create Workspace"
2. User enters name
3. POST /workspaces → creates in Supabase
4. Frontend navigates to canvas view

ADD PDF SOURCE
5. User clicks "Add Node" → sidebar opens
6. User clicks "PDF Source"
7. POST /sources → creates empty source record
8. Empty PDF node appears on canvas (200x120px)

UPLOAD PDF
9. User double-clicks PDF node → full screen modal opens
10. User clicks "Upload" → selects file
11. POST /sources/{id}/upload (multipart form)
12. Backend:
    a. Stores PDF in Supabase Storage
    b. Parses PDF with PyMuPDF
    c. Extracts chapters (title, pages, text)
    d. Caches full text with Gemini (gets cache_id)
    e. Stores metadata + cache_id in Supabase DB
13. Returns: { chapters, pdfUrl }
14. Frontend loads PDF viewer + chapter navigation in modal

GENERATE CODE LAB
15. User navigates to Chapter 5 in PDF viewer
16. User clicks "Generate Code Lab" in action panel
17. Modal opens: select chapter + language
18. POST /labs/generate { sourceId, chapterId, language }
19. Backend:
    a. Gets chapter text from DB
    b. Gets cache_id (recaches if expired)
    c. Calls Gemini with generation prompt
    d. Receives: { ai_solution, task_code, test_code, instructions }
    e. Validates: sends ai_solution + test_code to Judge0
    f. If fails: retry up to 3 times
    g. If still fails: return error
    h. Stores lab in Supabase DB
20. Returns: { labId, taskCode, testCode, instructions }
21. Code Lab node appears on canvas
22. Edge drawn from PDF → Code Lab

WORK IN CODE LAB
23. User double-clicks Code Lab node → full screen modal opens
24. Modal shows: Editor | Instructions | Tests | Results tabs
25. User writes code in Monaco editor
26. User clicks "Run Tests"
27. POST /labs/{id}/run { userCode }
28. Backend sends to Judge0, parses results
29. Returns: { tests: [{name, passed, error}], stdout }
30. Frontend shows results in Results tab
31. User iterates until all tests pass
32. "Submit & Close" button appears
33. User clicks "Submit & Close"
34. PATCH /labs/{id} { status: completed }
35. Modal closes
36. Code Lab card shows "✓ Completed" status

CONTINUE LEARNING
37. User returns to PDF, moves to Chapter 6
38. Repeat!
```

---

## 10. Technology Stack

### Frontend

| Technology      | Purpose                 |
| --------------- | ----------------------- |
| React 18        | UI framework            |
| TypeScript      | Type safety             |
| React Flow      | Canvas with nodes/edges |
| TanStack Router | Routing                 |
| Framer Motion   | Animations              |
| Monaco Editor   | Code editing            |
| react-pdf       | PDF viewing             |
| Xterm.js        | Terminal (future)       |

### Backend

| Technology  | Purpose         |
| ----------- | --------------- |
| FastAPI     | API framework   |
| Python 3.11 | Language        |
| PyMuPDF     | PDF parsing     |
| Pydantic    | Data validation |
| SQLAlchemy  | ORM (optional)  |

### Infrastructure

| Technology     | Purpose            |
| -------------- | ------------------ |
| Docker         | Containerization   |
| Docker Compose | Orchestration      |
| Supabase       | Database + Storage |
| Judge0         | Code execution     |
| Redis          | Judge0 dependency  |

### AI

| Technology        | Purpose             |
| ----------------- | ------------------- |
| Gemini            | Primary AI provider |
| Prompt caching    | Performance + cost  |
| Structured output | Reliable generation |

---

## 11. Database Schema

### Tables

```sql
-- Workspaces
CREATE TABLE workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Sources
CREATE TABLE sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,  -- 'pdf', 'github', etc.
    title VARCHAR(255) NOT NULL,
    storage_path VARCHAR(500),
    metadata JSONB,  -- chapters, etc.
    cache_id VARCHAR(255),
    cache_expires_at TIMESTAMP,
    canvas_position JSONB,  -- { x: number, y: number }
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Labs
CREATE TABLE labs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    source_id UUID REFERENCES sources(id) ON DELETE SET NULL,
    type VARCHAR(50) NOT NULL,  -- 'code_lab', 'flashcard_lab', etc.
    config JSONB,  -- { language, chapter_id, etc. }
    generated_content JSONB,  -- { task_code, test_code, instructions }
    user_state JSONB,  -- { user_code, test_results, progress }
    status VARCHAR(20) DEFAULT 'in_progress',  -- 'in_progress', 'completed'
    canvas_position JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Chat Messages
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- 'user', 'assistant'
    content TEXT NOT NULL,
    mentions JSONB,  -- ['source_123', 'lab_456']
    created_at TIMESTAMP DEFAULT NOW()
);

-- Edges (connections between nodes)
CREATE TABLE edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    source_node_id UUID NOT NULL,
    target_node_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 12. API Endpoints

### Workspaces

```
POST   /workspaces              Create workspace
GET    /workspaces              List workspaces
GET    /workspaces/{id}         Get workspace (with sources, labs, chat)
DELETE /workspaces/{id}         Delete workspace
```

### Sources

```
POST   /sources                      Create empty source
POST   /sources/{id}/upload          Upload content (PDF file)
GET    /sources/{id}                 Get source view data
PATCH  /sources/{id}                 Update source (e.g., current chapter)
DELETE /sources/{id}                 Delete source
GET    /sources/{id}/content/{ref}   Get specific content (e.g., chapter text)
```

### Labs

```
POST   /labs/generate                Generate new lab
GET    /labs/{id}                    Get lab view data
PATCH  /labs/{id}                    Update lab state (user code, etc.)
POST   /labs/{id}/run                Run tests
POST   /labs/{id}/action/{action}    Execute action (download, reset)
DELETE /labs/{id}                    Delete lab
```

### Chat

```
POST   /chat                         Send message, get response
GET    /chat/history/{workspace_id}  Get chat history
```

### Canvas

```
PATCH  /canvas/positions             Batch update node positions
POST   /canvas/edges                 Create edge
DELETE /canvas/edges/{id}            Delete edge
```

---

## 13. Contributor Guide

### Adding a New Lab Type

**Step 1: Create Backend Class**

Create `/backend/labs/flashcard_lab.py`:

```python
from app.labs.base import Lab, register_lab
from typing import Dict, Any, List

@register_lab
class FlashcardLab(Lab):
    lab_type = "flashcard_lab"

    cards: List[Dict[str, str]]  # [{front, back, status}]
    current_index: int = 0

    @classmethod
    def get_generation_prompt(cls, content: str, config: Dict[str, Any]) -> str:
        return f"""
        Generate flashcards from this educational content.

        Content:
        {content}

        Create 10-20 flashcards that help memorize key concepts.
        Each card should have:
        - front: Question or term
        - back: Answer or definition

        Focus on important concepts, not trivial details.
        """

    @classmethod
    def get_output_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "cards": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "front": {"type": "string"},
                            "back": {"type": "string"}
                        },
                        "required": ["front", "back"]
                    },
                    "minItems": 5,
                    "maxItems": 30
                }
            },
            "required": ["cards"]
        }

    async def initialize(self, generated_data: Dict[str, Any]) -> None:
        self.cards = [
            {"front": c["front"], "back": c["back"], "status": "unseen"}
            for c in generated_data["cards"]
        ]
        self.current_index = 0
        self.status = "in_progress"

    def is_complete(self) -> bool:
        return all(card["status"] == "known" for card in self.cards)

    def get_view_data(self) -> Dict[str, Any]:
        return {
            "type": "flashcard_lab",
            "cards": self.cards,
            "current_index": self.current_index,
            "progress": {
                "known": len([c for c in self.cards if c["status"] == "known"]),
                "total": len(self.cards)
            },
            "is_complete": self.is_complete(),
        }

    def get_actions(self) -> List[Dict[str, Any]]:
        return [
            {"id": "export_anki", "label": "Export to Anki"},
            {"id": "shuffle", "label": "Shuffle Cards"},
            {"id": "reset", "label": "Reset Progress"},
        ]
```

**Step 2: Create Frontend Renderer**

Create `/frontend/components/labs/FlashcardLabView.tsx`:

```typescript
// This is PURELY rendering — no business logic
interface FlashcardLabViewProps {
  data: {
    type: "flashcard_lab";
    cards: Array<{ front: string; back: string; status: string }>;
    current_index: number;
    progress: { known: number; total: number };
    is_complete: boolean;
  };
  onUpdateState: (state: any) => void;
}

export function FlashcardLabView({
  data,
  onUpdateState,
}: FlashcardLabViewProps) {
  const [flipped, setFlipped] = useState(false);
  const card = data.cards[data.current_index];

  const markCard = (status: "known" | "review") => {
    onUpdateState({
      card_index: data.current_index,
      status: status,
      next_index: (data.current_index + 1) % data.cards.length,
    });
    setFlipped(false);
  };

  return (
    <div className="flashcard-lab">
      <ProgressBar value={data.progress.known} max={data.progress.total} />

      <div
        className={`card ${flipped ? "flipped" : ""}`}
        onClick={() => setFlipped(!flipped)}
      >
        <div className="front">{card.front}</div>
        <div className="back">{card.back}</div>
      </div>

      <div className="actions">
        <button onClick={() => markCard("review")}>Review Again</button>
        <button onClick={() => markCard("known")}>I Know This</button>
      </div>

      {data.is_complete && (
        <div className="complete">🎉 All cards mastered!</div>
      )}
    </div>
  );
}
```

**Step 3: Register in Frontend**

Add to `/frontend/components/labs/LabModal.tsx`:

```typescript
import { FlashcardLabView } from "./FlashcardLabView";

function LabModal({ labId }) {
  const { data } = useQuery(["lab", labId], () => api.getLab(labId));

  switch (data.type) {
    case "code_lab":
      return <CodeLabView data={data} />;
    case "flashcard_lab":
      return <FlashcardLabView data={data} />; // Add this line
    default:
      return <GenericLabView data={data} />;
  }
}
```

**That's it!** The new lab type:

- Appears in generation options automatically (registry)
- Works with chat @mentions (generic interface)
- Persists correctly (base class handles it)
- Renders in modal (switch statement)

### What Contributors DON'T Touch

- Canvas code
- Sidebar code (lab types come from registry)
- Chat code (generic interface)
- Backend generation orchestration
- Core abstract classes

---

## 14. MVP Scope

### Building Now

**Sources:**

- ✅ PDF only

**Labs:**

- ✅ Code Lab only
- ✅ Python only

**Features:**

- ✅ Create workspace
- ✅ Upload PDF, see chapters
- ✅ Generate code lab from chapter
- ✅ Write code in Monaco editor
- ✅ Run tests via Judge0
- ✅ See pass/fail results
- ✅ Chat with @mentions (Socratic method)
- ✅ n8n-style canvas (cards + modal)
- ✅ Node connections (edges)

### Not Building Yet

**Sources:**

- ❌ GitHub repository source
- ❌ YouTube video source
- ❌ Documentation/URL source

**Labs:**

- ❌ Flashcard lab
- ❌ Quiz lab
- ❌ Terminal lab

**Features:**

- ❌ Multiple programming languages
- ❌ User accounts / authentication
- ❌ Progress tracking across sessions
- ❌ Lab-to-lab connections (data flow)
- ❌ Collaboration / sharing
- ❌ Templates / presets

---

## 15. Prototype Specification

### Goal

Build minimal React app to validate the n8n-style UI pattern works for our use case.

**Question to answer:** Does small cards + modal pattern feel right?

### What to Build

1. **Left Sidebar**

   - Buttons: Add PDF, Add Code Lab, Add Chat
   - On click → Creates node on canvas

2. **Canvas (React Flow)**

   - Small card nodes (200x120px)
   - Draggable
   - Connectable
   - Mini-map, controls, background

3. **Modal**
   - Opens on double-click
   - Full-screen overlay (1200x90vh)
   - Placeholder content
   - Close button (click outside or X)

### Setup

```bash
npm create vite@latest codex-prototype -- --template react-ts
cd codex-prototype
npm install @xyflow/react framer-motion lucide-react
npm run dev
```

### File Structure

```
src/
├── App.tsx              # Main component
├── types.ts             # Interfaces
├── components/
│   ├── Sidebar.tsx      # Left panel
│   ├── NodeModal.tsx    # Full view modal
│   └── nodes/
│       └── Cards.tsx    # Card components
```

### Success Criteria

After building, verify:

1. ✅ Can add nodes from sidebar easily
2. ✅ Small cards don't feel cramped
3. ✅ Double-click to modal feels natural
4. ✅ Modal provides enough space
5. ✅ Canvas organization makes sense
6. ✅ Can imagine scaling to 10+ nodes

### Time Budget

2 hours maximum. This is throwaway validation code.

---

## 16. Open Questions

### For Implementation

1. **PDF parsing library** — PyMuPDF or pdfplumber? Need to test chapter extraction quality.

2. **Error handling** — How to surface generation failures to user? Toast? Modal? Inline?

3. **Loading states** — Generation can take 10-30 seconds. What does user see?

4. **Offline support** — Any consideration for PWA / offline mode?

5. **Test output parsing** — Different frameworks (pytest, unittest, jest) have different outputs. Need robust parser.

### For Design

1. **Empty states** — What does empty workspace look like? Empty source before upload?

2. **Onboarding** — How does first-time user know what to do?

3. **Keyboard shortcuts** — What shortcuts make sense? (Cmd+Enter to run tests?)

4. **Mobile** — Any mobile consideration or desktop-only?

---

## Summary Table

| Concern                     | Where it lives                     |
| --------------------------- | ---------------------------------- |
| What is a Source/Lab        | Backend abstract class             |
| How to generate content     | Backend concrete class             |
| How to validate generation  | Backend concrete class             |
| What state to track         | Backend concrete class             |
| All business logic          | Backend                            |
| Caching logic               | Backend abstract class (automatic) |
| What data frontend receives | Backend `get_view_data()`          |
| How to render that data     | Frontend (dumb components)         |

---

## Quick Reference

### Docker Compose (Target)

```yaml
version: "3.8"
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - SUPABASE_URL=http://supabase:8000
      - JUDGE0_URL=http://judge0:2358
    depends_on:
      - supabase
      - judge0

  supabase:
    image: supabase/postgres
    # ... config

  judge0:
    image: judge0/judge0
    # ... config

  redis:
    image: redis:alpine
    # Judge0 dependency
```

### Key Files to Create

```
/backend
├── app/
│   ├── main.py              # FastAPI app
│   ├── sources/
│   │   ├── base.py          # Abstract Source class
│   │   └── pdf.py           # PDFSource
│   ├── labs/
│   │   ├── base.py          # Abstract Lab class
│   │   └── code_lab.py      # CodeLab
│   ├── services/
│   │   ├── ai.py            # AI provider interface
│   │   ├── judge0.py        # Code execution
│   │   └── storage.py       # Supabase integration
│   └── routes/
│       ├── workspaces.py
│       ├── sources.py
│       ├── labs.py
│       └── chat.py

/frontend
├── src/
│   ├── App.tsx
│   ├── components/
│   │   ├── Canvas.tsx       # React Flow wrapper
│   │   ├── Sidebar.tsx
│   │   ├── Modal.tsx
│   │   ├── nodes/           # Card components
│   │   └── labs/            # Lab view components
│   ├── hooks/
│   │   └── useWorkspace.ts
│   └── api/
│       └── client.ts        # API client
```

---

_This document represents the complete context for AIDE. Use it as the source of truth for implementation._

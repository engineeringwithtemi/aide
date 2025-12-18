# Code Review Guidelines for AIDE

**Standards:** Google/Anthropic Engineering Excellence
**Last Updated:** December 18, 2025
**Applies To:** All backend Python code, API endpoints, and infrastructure

---

## Review Philosophy

Code reviews are not gatekeeping—they're collaborative quality assurance. Every review should:

1. **Maintain architectural integrity** - Ensure code aligns with convo.md specifications
2. **Catch bugs before production** - Look for logic errors, edge cases, race conditions
3. **Improve code quality** - Suggest better patterns, clearer names, simpler solutions
4. **Share knowledge** - Explain *why* changes are needed, not just *what* to change
5. **Be respectful and constructive** - Focus on code, not the person

---

## Review Checklist

Use this checklist for every code review. Mark items as:
- ✅ **PASS** - Meets standards
- ⚠️ **NEEDS WORK** - Has issues that must be fixed
- 💡 **SUGGESTION** - Optional improvement
- ❌ **BLOCK** - Critical issue, cannot merge

---

## 1. Architecture & Design

### 1.1 Alignment with Specification

**Question:** Does this code implement what convo.md specifies?

- [ ] ✅ Matches the abstract class contract (if implementing Source/Lab)
- [ ] ✅ Uses correct method signatures from specification
- [ ] ✅ Returns data structures that match `get_view_data()` format
- [ ] ✅ Follows the two-server split (backend = brain, frontend = renderer)
- [ ] ⚠️ Deviates from spec without documented reason
- [ ] ❌ Conflicts with locked-in architectural decisions

**Examples:**

```python
# ❌ BLOCK - Violates spec
class PDFSource(Source):
    def get_view_data(self):
        # Spec says return dict with "type", "storage_url", "chapters"
        return {"pdf_url": self.path}  # Wrong structure!

# ✅ PASS - Matches spec exactly
class PDFSource(Source):
    def get_view_data(self):
        return {
            "type": "pdf",
            "storage_url": self.storage_path,
            "chapters": [{"id": ch.id, "title": ch.title} for ch in self.chapters],
            "current_chapter_id": self.current_chapter_id,
        }
```

### 1.2 Abstraction & Extensibility

**Question:** Can this code be extended without modification?

- [ ] ✅ Uses abstract classes where appropriate
- [ ] ✅ New types can be added without changing existing code
- [ ] ✅ No type-checking (if/elif chains based on type strings)
- [ ] ✅ Uses polymorphism and duck typing
- [ ] ⚠️ Hard-codes logic for specific types
- [ ] ❌ Requires modifying multiple files to add a new type

**Examples:**

```python
# ❌ BLOCK - Hard-coded type checking
def generate_lab(source: Source):
    if source.type == "pdf":
        content = source.chapters[0].text  # Assumes PDF structure!
    elif source.type == "github":
        content = source.files[0].content  # Assumes GitHub structure!
    # Adding new source type requires changing this function!

# ✅ PASS - Generic interface
def generate_lab(source: Source):
    content = await source.get_content_for_generation(context)
    # Works for ANY source type that implements the abstract method!
```

### 1.3 Separation of Concerns

**Question:** Is each component doing one thing well?

- [ ] ✅ Business logic in services, not routes
- [ ] ✅ Data validation in Pydantic models
- [ ] ✅ Database access in `app/services/db.py`
- [ ] ✅ External API calls in dedicated service files
- [ ] ⚠️ Routes contain complex business logic
- [ ] ❌ Mixed concerns (e.g., route that also talks to database directly)

**Examples:**

```python
# ❌ BLOCK - Mixed concerns
@router.post("/labs/generate")
async def generate_lab(request: GenerateLabRequest):
    # Route should NOT do database access directly
    source = await db.execute(f"SELECT * FROM sources WHERE id = {request.source_id}")
    # Route should NOT contain AI logic
    response = await gemini.generate(prompt, schema)
    # Route should NOT do validation logic
    if not response["task_code"]:
        raise ValueError("Invalid response")
    return response

# ✅ PASS - Proper separation
@router.post("/labs/generate")
async def generate_lab(request: GenerateLabRequest):
    # Delegate to service
    lab = await lab_service.generate_lab(
        source_id=request.source_id,
        lab_type=request.lab_type,
        config=request.config
    )
    return LabResponse.from_orm(lab)
```

---

## 2. Code Quality

### 2.1 Readability & Clarity

**Question:** Can another engineer understand this code in 5 minutes?

- [ ] ✅ Variable names clearly indicate purpose
- [ ] ✅ Functions have single, clear purpose
- [ ] ✅ Complex logic has explanatory comments
- [ ] ✅ No magic numbers or strings
- [ ] ⚠️ Names are vague (e.g., `data`, `temp`, `x`)
- [ ] ❌ Logic is convoluted or clever without reason

**Examples:**

```python
# ❌ BLOCK - Unclear, magic numbers
def p(c):
    return c > 15 and len(c.t) > 100

# ✅ PASS - Clear intent
def is_valid_chapter_for_generation(chapter: Chapter) -> bool:
    """Check if chapter has enough content to generate a lab.

    Requirements:
    - At least 15 pages (ensures sufficient content)
    - At least 100 words (ensures meaningful text)
    """
    MIN_PAGES = 15
    MIN_WORDS = 100
    return chapter.page_count >= MIN_PAGES and len(chapter.text.split()) >= MIN_WORDS
```

### 2.2 Type Safety

**Question:** Are types properly annotated and checked?

- [ ] ✅ All function signatures have type hints
- [ ] ✅ Return types are specified
- [ ] ✅ Pydantic models used for data validation
- [ ] ✅ Optional types marked with `Optional[T]` or `T | None`
- [ ] ⚠️ Missing type hints on public functions
- [ ] ❌ Uses `Any` without justification
- [ ] ❌ Type hints don't match implementation

**Examples:**

```python
# ❌ BLOCK - Missing types, using Any
def process(data):  # What type is data?
    result = transform(data)  # What does this return?
    return result

# ✅ PASS - Proper typing
def process_chapter_text(raw_text: str) -> dict[str, Any]:
    """Extract structured data from chapter text.

    Returns:
        Dictionary with 'title', 'content', and 'metadata' keys.
    """
    parsed = parse_markdown(raw_text)
    return {
        "title": parsed.title,
        "content": parsed.content,
        "metadata": parsed.frontmatter,
    }
```

### 2.3 Error Handling

**Question:** Does this code handle errors gracefully?

- [ ] ✅ Explicit error handling for external APIs (AI, Judge0, Database)
- [ ] ✅ User-friendly error messages
- [ ] ✅ Proper HTTP status codes (400, 404, 500, etc.)
- [ ] ✅ Logging for debugging
- [ ] ✅ Retries for transient failures (with backoff)
- [ ] ⚠️ Bare `except:` clauses
- [ ] ❌ Swallows errors silently
- [ ] ❌ Exposes internal details to users

**Examples:**

```python
# ❌ BLOCK - Poor error handling
async def generate_lab(source_id: str):
    try:
        source = await db.get_source(source_id)
        lab = await ai_provider.generate(source.content)
        return lab
    except:  # Catches everything! Database, network, AI errors...
        return None  # User gets no information about what went wrong

# ✅ PASS - Proper error handling
async def generate_lab(source_id: str) -> Lab:
    """Generate a lab from a source.

    Raises:
        HTTPException(404): Source not found
        HTTPException(500): AI generation failed after retries
    """
    # 1. Validate source exists
    source = await db.get_source(source_id)
    if not source:
        logger.warning(f"Source not found: {source_id}")
        raise HTTPException(404, "Source not found")

    # 2. Try generation with retries
    for attempt in range(3):
        try:
            lab = await ai_provider.generate(
                prompt=source.get_generation_prompt(),
                schema=Lab.get_output_schema()
            )
            logger.info(f"Generated lab for source {source_id}")
            return lab
        except AIProviderError as e:
            logger.warning(f"Generation attempt {attempt + 1} failed: {e}")
            if attempt == 2:
                # Final attempt failed
                raise HTTPException(
                    500,
                    "Failed to generate lab after 3 attempts. Please try again."
                )
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### 2.4 Performance

**Question:** Is this code efficient?

- [ ] ✅ No N+1 query problems
- [ ] ✅ Appropriate use of async/await
- [ ] ✅ Database queries use indexes
- [ ] ✅ Large data uses pagination
- [ ] ✅ Caching where appropriate
- [ ] ⚠️ Synchronous blocking calls in async functions
- [ ] ❌ Loads entire dataset into memory
- [ ] ❌ Unnecessary loops or redundant operations

**Examples:**

```python
# ❌ BLOCK - N+1 query problem
async def get_workspace_with_sources(workspace_id: str):
    workspace = await db.get_workspace(workspace_id)
    sources = []
    for source_id in workspace.source_ids:
        source = await db.get_source(source_id)  # Separate query per source!
        sources.append(source)
    workspace.sources = sources
    return workspace

# ✅ PASS - Single query
async def get_workspace_with_sources(workspace_id: str):
    workspace = await db.get_workspace(workspace_id)
    # Fetch all sources in one query
    sources = await db.get_sources_by_ids(workspace.source_ids)
    workspace.sources = sources
    return workspace
```

```python
# ❌ BLOCK - Blocking call in async function
async def parse_pdf(file_path: str):
    pdf = PyMuPDF.open(file_path)  # Synchronous file I/O blocks event loop!
    text = pdf[0].get_text()
    return text

# ✅ PASS - Async file I/O
async def parse_pdf(file_path: str):
    async with aiofiles.open(file_path, 'rb') as f:
        content = await f.read()
    # Use thread pool for CPU-intensive parsing
    loop = asyncio.get_event_loop()
    text = await loop.run_in_executor(None, _parse_pdf_sync, content)
    return text
```

---

## 3. Security

### 3.1 Input Validation

**Question:** Is user input properly validated?

- [ ] ✅ Pydantic models validate all request data
- [ ] ✅ File uploads check file type and size
- [ ] ✅ SQL queries use parameterization (no string interpolation)
- [ ] ✅ Path traversal prevented (file uploads, PDF access)
- [ ] ⚠️ Validates format but not content
- [ ] ❌ Accepts raw user input without validation
- [ ] ❌ SQL injection possible

**Examples:**

```python
# ❌ BLOCK - SQL injection vulnerability
async def get_workspace(name: str):
    query = f"SELECT * FROM workspaces WHERE name = '{name}'"  # NEVER DO THIS!
    return await db.execute(query)

# ✅ PASS - Parameterized query
async def get_workspace(name: str):
    query = "SELECT * FROM workspaces WHERE name = $1"
    return await db.execute(query, name)
```

```python
# ❌ BLOCK - Path traversal vulnerability
@router.get("/pdfs/{filename}")
async def get_pdf(filename: str):
    # User can pass "../../etc/passwd"
    return FileResponse(f"/app/pdfs/{filename}")

# ✅ PASS - Validated path
@router.get("/pdfs/{source_id}")
async def get_pdf(source_id: str):
    source = await db.get_source(source_id)
    if not source:
        raise HTTPException(404, "Source not found")
    # Use source.storage_path which is controlled by us
    return FileResponse(source.storage_path)
```

### 3.2 Secrets Management

**Question:** Are secrets handled securely?

- [ ] ✅ No secrets in code or logs
- [ ] ✅ API keys from environment variables
- [ ] ✅ Secrets not logged or exposed in errors
- [ ] ⚠️ Secrets in comments or docstrings
- [ ] ❌ Hard-coded API keys
- [ ] ❌ Secrets in version control

**Examples:**

```python
# ❌ BLOCK - Hard-coded secret
gemini_api_key = "AIzaSyD..."  # NEVER commit this!

# ✅ PASS - From environment
from app.config import settings

gemini_api_key = settings.gemini_api_key  # Loaded from .env
```

### 3.3 Authorization

**Question:** Is access properly controlled?

- [ ] ✅ Users can only access their own workspaces
- [ ] ✅ Resource existence checked before operations
- [ ] ✅ Workspace ownership validated
- [ ] ⚠️ Assumes authorization is handled elsewhere
- [ ] ❌ No authorization checks
- [ ] ❌ User can access other users' data

**Note:** MVP doesn't have user accounts, but architecture should support adding them later.

---

## 4. Testing

### 4.1 Test Coverage

**Question:** Can we verify this code works?

- [ ] ✅ Unit tests for core logic
- [ ] ✅ Integration tests for external services (with mocks)
- [ ] ✅ Edge cases tested (empty input, null values, errors)
- [ ] ✅ Happy path tested
- [ ] ⚠️ Only happy path tested
- [ ] ❌ No tests provided

**Refer to TESTING_GUIDE.md for detailed testing standards.**

### 4.2 Testability

**Question:** Is this code easy to test?

- [ ] ✅ Pure functions where possible
- [ ] ✅ Dependencies injected (not hard-coded)
- [ ] ✅ External services mockable
- [ ] ✅ Database operations use service layer
- [ ] ⚠️ Heavy coupling to external services
- [ ] ❌ Impossible to test without real AI/database

**Examples:**

```python
# ❌ BLOCK - Hard to test
async def generate_lab():
    # Hard-coded dependency - can't mock in tests!
    response = await GeminiProvider().generate(prompt)
    return response

# ✅ PASS - Dependency injection
async def generate_lab(ai_provider: AIProvider):
    # Can pass a MockAIProvider in tests
    response = await ai_provider.generate(prompt)
    return response
```

---

## 5. API Design

### 5.1 RESTful Conventions

**Question:** Does the API follow REST principles?

- [ ] ✅ Proper HTTP methods (GET, POST, PATCH, DELETE)
- [ ] ✅ Meaningful resource paths
- [ ] ✅ Consistent response formats
- [ ] ✅ Proper status codes
- [ ] ⚠️ Uses GET for mutations
- [ ] ❌ Inconsistent path structure

**Examples:**

```python
# ❌ BLOCK - Poor REST design
@router.get("/delete-workspace")  # Should be DELETE!
async def delete_workspace(id: str):
    ...

@router.post("/workspace-list")  # Should be GET!
async def list_workspaces():
    ...

# ✅ PASS - Proper REST
@router.delete("/workspaces/{workspace_id}")
async def delete_workspace(workspace_id: str):
    ...

@router.get("/workspaces")
async def list_workspaces():
    ...
```

### 5.2 Request/Response Models

**Question:** Are API contracts clear and validated?

- [ ] ✅ Pydantic models for all requests/responses
- [ ] ✅ Clear field names and types
- [ ] ✅ Optional fields marked explicitly
- [ ] ✅ Examples in docstrings
- [ ] ⚠️ Uses generic dicts instead of models
- [ ] ❌ No validation

**Examples:**

```python
# ❌ BLOCK - No validation
@router.post("/labs/generate")
async def generate_lab(data: dict):  # What fields are required?
    source_id = data.get("source_id")  # Might be missing!
    lab_type = data.get("lab_type")
    ...

# ✅ PASS - Proper models
class GenerateLabRequest(BaseModel):
    """Request to generate a new lab."""
    source_id: str
    lab_type: str
    chapter_id: Optional[str] = None
    config: dict[str, Any] = {}

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source_id": "src_123",
                "lab_type": "code_lab",
                "chapter_id": "ch_5",
                "config": {"language": "python"}
            }
        }
    )

@router.post("/labs/generate")
async def generate_lab(request: GenerateLabRequest):
    # Validation happens automatically!
    ...
```

---

## 6. Documentation

### 6.1 Code Documentation

**Question:** Can someone understand this code without running it?

- [ ] ✅ Docstrings on all public functions/classes
- [ ] ✅ Complex logic has inline comments
- [ ] ✅ Docstrings follow Google style
- [ ] ✅ Examples for non-obvious usage
- [ ] ⚠️ Comments explain "what" instead of "why"
- [ ] ❌ No documentation

**Examples:**

```python
# ❌ BLOCK - No docstring
def validate_generation(generated: dict, test_code: str):
    result = execute_code(generated["ai_solution"], test_code)
    return result.all_passed

# ✅ PASS - Clear documentation
async def validate_generation(
    generated: dict[str, Any],
    test_code: str
) -> bool:
    """Validate AI-generated lab by running solution against tests.

    This is critical for quality control - we never show a lab to the user
    unless we've verified that the AI's solution actually passes the tests.

    Args:
        generated: AI output containing 'ai_solution', 'task_code', 'test_code'
        test_code: Test code to run against solution

    Returns:
        True if all tests pass, False otherwise

    Raises:
        Judge0Error: If code execution fails

    Example:
        >>> generated = {"ai_solution": "def add(a, b): return a + b", ...}
        >>> await validate_generation(generated, "assert add(2, 3) == 5")
        True
    """
    result = await judge0_service.execute_code(
        code=generated["ai_solution"],
        test_code=test_code,
        language="python"
    )
    return result.all_passed
```

### 6.2 API Documentation

**Question:** Can frontend developers use this API?

- [ ] ✅ OpenAPI/Swagger docs generated
- [ ] ✅ Endpoint descriptions clear
- [ ] ✅ Request/response examples provided
- [ ] ✅ Error codes documented
- [ ] ⚠️ Missing examples
- [ ] ❌ No API documentation

---

## 7. Maintainability

### 7.1 Code Duplication

**Question:** Is logic reused appropriately?

- [ ] ✅ Common patterns extracted to utilities
- [ ] ✅ DRY principle followed (Don't Repeat Yourself)
- [ ] ✅ Shared logic in service layer
- [ ] ⚠️ Minor duplication (acceptable if aids clarity)
- [ ] ❌ Same logic copy-pasted in multiple places

**Examples:**

```python
# ❌ BLOCK - Duplicated logic
@router.post("/labs/generate")
async def generate_lab(request):
    cache_id = source.cache_id
    if not cache_id or datetime.utcnow() > source.cache_expires_at:
        cache_id = await ai_provider.create_cache(source.get_full_content())
    # ... rest of logic

@router.post("/chat")
async def chat(request):
    # Same caching logic copy-pasted!
    cache_id = source.cache_id
    if not cache_id or datetime.utcnow() > source.cache_expires_at:
        cache_id = await ai_provider.create_cache(source.get_full_content())
    # ... rest of logic

# ✅ PASS - Logic in Source abstract class
# Both routes just call source.get_cache_id()
```

### 7.2 Configurability

**Question:** Can behavior be changed without code changes?

- [ ] ✅ Magic numbers in config/constants
- [ ] ✅ Feature flags for experimental features
- [ ] ✅ Environment-specific settings
- [ ] ⚠️ Some hard-coded values
- [ ] ❌ All behavior hard-coded

**Examples:**

```python
# ❌ BLOCK - Hard-coded values
async def generate_lab():
    for attempt in range(3):  # Why 3? What if we want to change it?
        if await validate_generation(lab):
            break
        await asyncio.sleep(2)  # Why 2 seconds?

# ✅ PASS - Configurable
class GenerationConfig:
    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 2
    VALIDATION_TIMEOUT = 30

async def generate_lab():
    config = GenerationConfig()
    for attempt in range(config.MAX_RETRIES):
        if await validate_generation(lab, timeout=config.VALIDATION_TIMEOUT):
            break
        await asyncio.sleep(config.RETRY_DELAY_SECONDS)
```

---

## 8. Specific to AIDE Architecture

### 8.1 Abstract Class Implementation

**Question:** Does this correctly implement the abstract interface?

- [ ] ✅ All abstract methods implemented
- [ ] ✅ Method signatures match exactly
- [ ] ✅ Return types match specification
- [ ] ✅ Registered with decorator (@register_source/@register_lab)
- [ ] ⚠️ Adds extra methods not in spec (document why)
- [ ] ❌ Missing required abstract methods
- [ ] ❌ Wrong signatures

**Examples:**

```python
# ❌ BLOCK - Wrong signature
class CodeLab(Lab):
    # Spec says: get_generation_prompt(cls, content: str, config: Dict)
    def get_generation_prompt(content):  # Missing cls, config!
        return f"Generate from: {content}"

# ✅ PASS - Correct implementation
@register_lab
class CodeLab(Lab):
    lab_type = "code_lab"

    @classmethod
    def get_generation_prompt(
        cls,
        content: str,
        config: dict[str, Any]
    ) -> str:
        language = config.get("language", "python")
        return f"""
        Create a coding exercise from this content.

        Content: {content}
        Language: {language}

        Return JSON with: instructions, task_code, test_code, ai_solution
        """
```

### 8.2 Caching Behavior

**Question:** Is caching handled correctly?

- [ ] ✅ Source class uses automatic caching (doesn't reimplement)
- [ ] ✅ `get_full_content()` returns all content for caching
- [ ] ✅ Cache invalidation works
- [ ] ⚠️ Implements own caching (should use abstract class)
- [ ] ❌ Doesn't cache at all
- [ ] ❌ Breaks cache invalidation

### 8.3 Frontend Data Contract

**Question:** Does `get_view_data()` return the right structure?

- [ ] ✅ Returns dict matching frontend expectations
- [ ] ✅ Includes all required fields
- [ ] ✅ Never includes sensitive data (e.g., ai_solution)
- [ ] ⚠️ Includes extra fields (document why)
- [ ] ❌ Wrong structure
- [ ] ❌ Exposes internal implementation details

### 8.4 Validation Before Display

**Question:** Is AI output validated before showing to user?

- [ ] ✅ Labs validate AI solution passes tests
- [ ] ✅ Retry logic (up to 3 attempts)
- [ ] ✅ User sees error if all attempts fail
- [ ] ❌ Shows unvalidated AI output
- [ ] ❌ No retry logic

---

## 9. Review Process

### 9.1 For the Reviewer

When reviewing code, follow this process:

1. **Read the specification** (task.md, convo.md)
   - What is this code supposed to do?
   - What are the acceptance criteria?

2. **High-level review first**
   - Does the architecture make sense?
   - Is it in the right place?
   - Does it follow the abstract class pattern?

3. **Detailed review**
   - Go through the checklist above
   - Look for bugs, edge cases, security issues
   - Check code quality and readability

4. **Suggest improvements**
   - Explain *why* changes are needed
   - Provide examples of better patterns
   - Link to documentation or similar code

5. **Test the code** (if possible)
   - Run existing tests
   - Try edge cases manually
   - Verify it integrates with other components

### 9.2 Review Comments Format

Use this format for review comments:

```markdown
## [BLOCK/NEEDS WORK/SUGGESTION] Issue Title

**Location:** `app/sources/pdf.py:45-52`

**Issue:** Brief description of the problem

**Why this matters:** Explain the impact (security, bugs, maintainability)

**Suggested fix:**
```python
# Show the corrected code
```

**References:**
- [Link to specification](convo.md#section)
- [Link to similar code](app/labs/base.py:100)
```

### 9.3 Example Review

```markdown
## ❌ BLOCK: Missing Input Validation

**Location:** `app/routes/v1/sources.py:23-30`

**Issue:** File upload doesn't validate file type or size

```python
@router.post("/sources/{id}/upload")
async def upload_pdf(file: UploadFile):
    content = await file.read()  # No size limit!
    await storage.save(content)  # No type check!
```

**Why this matters:**
- Security: User could upload malware or non-PDF files
- Stability: Large files could exhaust memory
- User experience: Uploading non-PDFs fails later with cryptic error

**Suggested fix:**
```python
@router.post("/sources/{id}/upload")
async def upload_pdf(file: UploadFile):
    # Validate file type
    if not file.content_type == "application/pdf":
        raise HTTPException(400, "Only PDF files are supported")

    # Validate size (max 50MB)
    MAX_SIZE = 50 * 1024 * 1024
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(413, "File too large (max 50MB)")

    await storage.save(content)
```

**References:**
- [Security checklist](#31-input-validation)
- [Similar validation in test fixture](tests/conftest.py:45)
```

---

## 10. Common Pitfalls to Watch For

### 10.1 Async/Await Mistakes

```python
# ❌ WRONG - Forgetting await
async def get_workspace(id: str):
    workspace = db.get_workspace(id)  # Returns coroutine, not result!
    return workspace

# ✅ CORRECT
async def get_workspace(id: str):
    workspace = await db.get_workspace(id)
    return workspace
```

### 10.2 Mutable Default Arguments

```python
# ❌ WRONG - Mutable default is shared across calls
def generate_lab(config={}):
    config["timestamp"] = datetime.now()  # Modifies shared dict!
    return config

# ✅ CORRECT
def generate_lab(config=None):
    config = config or {}
    config["timestamp"] = datetime.now()
    return config
```

### 10.3 Catching Too Broad

```python
# ❌ WRONG - Catches everything including KeyboardInterrupt
try:
    result = await ai_provider.generate(prompt)
except:  # Too broad!
    return None

# ✅ CORRECT - Catch specific exceptions
try:
    result = await ai_provider.generate(prompt)
except AIProviderError as e:
    logger.error(f"Generation failed: {e}")
    raise HTTPException(500, "Generation failed")
```

### 10.4 Not Closing Resources

```python
# ❌ WRONG - File not closed if error occurs
async def process_pdf(path: str):
    file = await aiofiles.open(path)
    data = await file.read()
    return process(data)  # If this raises, file stays open!

# ✅ CORRECT - Use context manager
async def process_pdf(path: str):
    async with aiofiles.open(path) as file:
        data = await file.read()
    return process(data)  # File always closed
```

---

## 11. When to Be Strict vs. Pragmatic

### Be Strict About:
- **Security issues** - Always block
- **Architectural violations** - Affects future extensibility
- **Data integrity** - Database constraints, validation
- **Breaking changes to APIs** - Frontend depends on us
- **Missing error handling** - Causes production issues

### Be Pragmatic About:
- **Minor style issues** - If linter doesn't catch it, it's probably fine
- **Premature optimization** - "Make it work, then make it fast"
- **Over-engineering** - YAGNI (You Aren't Gonna Need It)
- **Perfect documentation** - Good enough is fine for internal code
- **Test coverage** - 80% is great, 100% is not necessary

---

## 12. Review Etiquette

### DO:
- ✅ Focus on the code, not the person
- ✅ Explain *why* something should change
- ✅ Provide examples and references
- ✅ Acknowledge good solutions
- ✅ Ask questions if you don't understand
- ✅ Offer to pair program on complex issues

### DON'T:
- ❌ Use absolute language ("This is wrong")
- ❌ Be condescending or sarcastic
- ❌ Nitpick trivial style issues (use linter!)
- ❌ Approve code you don't understand
- ❌ Block on personal preferences
- ❌ Review your own code

---

## 13. Conclusion

This review guideline aims to maintain Google/Anthropic-level code quality while being practical and respectful. Remember:

1. **Quality over speed** - It's cheaper to fix issues in review than in production
2. **Learn together** - Every review is a learning opportunity
3. **Maintain standards** - Consistency across the codebase matters
4. **Be kind** - We're all trying to build something great

For questions about this guideline or specific review scenarios, refer to:
- [convo.md](./convo.md) - Project specification
- [TESTING_GUIDE.md](./TESTING_GUIDE.md) - Testing standards
- [backend/LINTING_RULES.md](./backend/LINTING_RULES.md) - Linting rules

---

**Last Updated:** December 18, 2025
**Version:** 1.0
**Maintainer:** Engineering Team

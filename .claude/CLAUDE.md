# Project Context

Always consider these files when working on this project:

- See `aide/spec.md` for project scope and details
- See `aide/REVIEW_GUIDELINE.md` for code review guidelines
- See `aide/task.md` for tasks me the developer is working on.

## Development Guidelines

### Running Tests

```bash
make dkt              # Run tests in Docker (recommended)
```

This handles everything: starts test database, runs migrations, executes tests with coverage.

### Common Commands

| Command | Alias | Description |
|---------|-------|-------------|
| `make docker-test` | `dkt` | Run tests in Docker |
| `make docker-up` | `dku` | Start dev services |
| `make docker-down` | `dkd` | Stop services |
| `make backend-dev` | `bd` | Run backend locally |
| `make backend-check` | `bc` | Lint + format + type check + test |
| `make db-migrate` | - | Run alembic migrations |

### Database Migrations

```bash
cd backend && uv run alembic revision --autogenerate -m "description"
make db-migrate
```

### Testing Approach

- Integration tests only - test behavior via API endpoints
- Tests in `backend/tests/integration/`
- Mock external services (Supabase, Gemini), use real database
- Each test cleans up after itself

### Adding a New Feature

1. Modify models in `app/db/tables.py`
2. Create migration
3. Add service logic in `app/services/`
4. Add route in `app/routes/v1/`
5. Add integration test
6. Run `make dkt`

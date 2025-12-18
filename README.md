# AIDE - Active Interactive Development Environment

## A.I Driven Education

Tags: ["AI Driven Education"]

Transform passive learning materials into interactive practice tools.

## Quick Start

```bash
# Initial setup
make setup

# Start development
make dev

# Run checks before committing
make pre-commit

# Run full CI pipeline
make ci
```

## Documentation

- **[MAKEFILE_ALIASES.md](./MAKEFILE_ALIASES.md)** - Quick reference for short commands
- **[Makefile](./Makefile)** - Full command reference (`make help`)
- **[backend/LINTING_RULES.md](./backend/LINTING_RULES.md)** - Linting & type checking rules explained
- **[TESTING_GUIDE.md](./TESTING_GUIDE.md)** - Testing guidelines
- **[convo.md](./convo.md)** - Complete project specification

## Common Commands

### Aliases (Fast!)

```bash
# Backend
make bt       # backend-test
make bl       # backend-lint
make bf       # backend-format
make bd       # backend-dev
make bc       # backend-check

# Frontend
make ft       # frontend-test
make fl       # frontend-lint
make ff       # frontend-format
make fd       # frontend-dev
make fc       # frontend-check

# Combined
make t        # test (both)
make c        # check (both)
make x        # fix (both)
make d        # dev (both)
```

### Full Commands

```bash
# Development
make dev                    # Start both servers
make backend-dev           # Backend only (http://localhost:8000)
make frontend-dev          # Frontend only (http://localhost:3000)

# Quality Checks
make check                 # Run all checks
make backend-check         # Backend: lint + format + type + test
make frontend-check        # Frontend: lint + format + type + test

# Auto-fix
make fix                   # Fix all issues
make backend-fix           # Backend: fix lint + format
make frontend-fix          # Frontend: fix lint + format

# Testing
make test                  # All tests
make backend-test          # Backend tests with coverage
make backend-test-watch    # Backend tests in watch mode
make frontend-test         # Frontend tests
make frontend-test-watch   # Frontend tests in watch mode
```

## Project Structure

```
aide/
├── backend/                 # FastAPI backend
│   ├── app/                # Application code
│   ├── tests/              # Backend tests
│   └── pyproject.toml      # Python dependencies & config
├── frontend/               # React frontend (coming soon)
├── Makefile                # Development commands
└── docker-compose.yml      # Service orchestration
```

## Tech Stack

### Backend

- **Python 3.13** - Language
- **FastAPI** - API framework
- **Ruff** - Linting & formatting
- **Ty** - Type checking
- **Pytest** - Testing
- **uv** - Package manager

### Frontend (Coming Soon)

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **React Flow** - Canvas
- **Vitest** - Testing

### Infrastructure

- **Docker** - Containerization
- **Supabase** - Database & storage
- **Judge0** - Code execution
- **Gemini** - AI generation

## Development Workflow

### 1. Starting Work

```bash
git pull
make i              # Install dependencies (alias for 'make install')
make d              # Start dev servers (alias for 'make dev')
```

### 2. While Coding

```bash
# In one terminal
make bd             # Backend dev server

# In another terminal
make btw            # Backend tests in watch mode
```

### 3. Before Committing

```bash
make x              # Auto-fix all issues (alias for 'make fix')
make c              # Check everything passes (alias for 'make check')
```

### 4. Committing

```bash
git add .
git commit -m "feat: your changes"
```

### 5. Before Pushing

```bash
make ci             # Run CI pipeline locally
git push
```

## Key Features

- ✅ Comprehensive linting (Ruff with 15+ rule categories)
- ✅ Strict type checking (gradual adoption strategy)
- ✅ Fast testing (pytest with coverage)
- ✅ Auto-formatting (consistent code style)
- ✅ Short aliases (60% less typing!)
- ✅ Colored output (clear visual feedback)
- ✅ Docker support (one-command setup)
- ✅ CI/CD ready (same checks locally & in pipeline)

## Requirements

### Backend

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) package manager

### Frontend

- Node.js 18+
- npm or pnpm

### Docker (Optional)

- Docker Desktop or Docker Engine
- Docker Compose

## Installation

### Install uv (if not already installed)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Setup Project

```bash
# Clone repository
git clone <repository-url>
cd aide

# Install dependencies
make setup

# Start development
make dev
```

## Help & Support

```bash
make help           # Show all commands
make status         # Check project setup status
```

## Contributing

1. Read the [linting rules](./backend/LINTING_RULES.md)
2. Follow the [testing guide](./TESTING_GUIDE.md)
3. Use `make pre-commit` before committing
4. Ensure `make ci` passes before pushing

## License

[Add your license here]

## Questions?

- Check `make help` for all commands
- See [MAKEFILE_ALIASES.md](./MAKEFILE_ALIASES.md) for shortcuts
- Read [convo.md](./convo.md) for project context

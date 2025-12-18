# ============================================================================
# AIDE Project Makefile
# ============================================================================
# Handles linting, formatting, type checking, and testing for both backend and frontend
#
# Requirements:
#   - Backend: Python 3.13+, uv package manager
#   - Frontend: Node.js 18+, npm/pnpm
#
# Quick Start:
#   make help          - Show all available commands
#   make install       - Install all dependencies
#   make check         - Run all checks (lint, type, test)
#   make fix           - Auto-fix all issues
# ============================================================================

.PHONY: help
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# ============================================================================
# General Commands
# ============================================================================

help: ## Show this help message
	@echo "$(BLUE)AIDE Development Commands$(NC)"
	@echo ""
	@echo "$(GREEN)General:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}' | \
		grep -v "backend-\|frontend-\|Alias for"
	@echo ""
	@echo "$(GREEN)Backend:$(NC)"
	@grep -E '^backend-[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Frontend:$(NC)"
	@grep -E '^frontend-[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Aliases (Quick Shortcuts):$(NC)"
	@echo "  $(YELLOW)Backend:$(NC)  bi bd bl blf bf bfc bt btf btw bty bc bx bcl bsh"
	@echo "  $(YELLOW)Frontend:$(NC) fi fd fl flf ff ffc ft ftw fty fb fp fc fx fcl"
	@echo "  $(YELLOW)Docker:$(NC)   dkb dku dkd dkr dkl dkt dksh dkps dkcl"
	@echo "  $(YELLOW)Combined:$(NC) i d c x t cl"
	@echo ""
	@echo "  Tip: Run 'make <alias>' (e.g., 'make bt' for backend-test, 'make dku' for docker-up)"
	@echo "  See all aliases: grep '##.*Alias for' Makefile"

install: backend-install frontend-install ## Install all dependencies (backend + frontend)

clean: backend-clean frontend-clean ## Clean all build artifacts and caches

check: backend-check frontend-check ## Run all checks (lint + type + test)

fix: backend-fix frontend-fix ## Auto-fix all formatting and linting issues

test: backend-test frontend-test ## Run all tests

dev: ## Start both backend and frontend in development mode
	@echo "$(BLUE)Starting development servers...$(NC)"
	@trap 'kill 0' EXIT; \
		$(MAKE) backend-dev & \
		$(MAKE) frontend-dev & \
		wait

# ============================================================================
# Backend Commands (Python + FastAPI)
# ============================================================================

backend-install: ## Install backend dependencies using uv
	@echo "$(BLUE)Installing backend dependencies...$(NC)"
	cd backend && uv sync --dev
	@echo "$(GREEN)✓ Backend dependencies installed$(NC)"

backend-dev: ## Start backend development server
	@echo "$(BLUE)Starting backend server...$(NC)"
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

backend-lint: ## Run backend linting (ruff check)
	@echo "$(BLUE)Running backend linting...$(NC)"
	cd backend && uv run ruff check .
	@echo "$(GREEN)✓ Backend linting passed$(NC)"

backend-lint-fix: ## Auto-fix backend linting issues
	@echo "$(BLUE)Auto-fixing backend linting issues...$(NC)"
	cd backend && uv run ruff check --fix .
	@echo "$(GREEN)✓ Backend linting auto-fixed$(NC)"

backend-format: ## Format backend code (ruff format)
	@echo "$(BLUE)Formatting backend code...$(NC)"
	cd backend && uv run ruff format .
	@echo "$(GREEN)✓ Backend code formatted$(NC)"

backend-format-check: ## Check backend formatting without modifying files
	@echo "$(BLUE)Checking backend formatting...$(NC)"
	cd backend && uv run ruff format --check .
	@echo "$(GREEN)✓ Backend formatting is correct$(NC)"

backend-type: ## Run backend type checking (ty)
	@echo "$(BLUE)Running backend type checking...$(NC)"
	cd backend && uv run ty check
	@echo "$(GREEN)✓ Backend type checking passed$(NC)"

backend-test: ## Run backend tests with pytest
	@echo "$(BLUE)Running backend tests...$(NC)"
	cd backend && uv run pytest -v --cov=app --cov-report=term-missing
	@echo "$(GREEN)✓ Backend tests passed$(NC)"

backend-test-fast: ## Run backend tests without coverage (faster)
	@echo "$(BLUE)Running backend tests (fast mode)...$(NC)"
	cd backend && uv run pytest -v
	@echo "$(GREEN)✓ Backend tests passed$(NC)"

backend-test-watch: ## Run backend tests in watch mode
	@echo "$(BLUE)Running backend tests in watch mode...$(NC)"
	cd backend && uv run pytest-watch -v

backend-check: backend-lint backend-format-check backend-type backend-test ## Run all backend checks

backend-fix: backend-lint-fix backend-format ## Auto-fix all backend issues

backend-clean: ## Clean backend build artifacts and caches
	@echo "$(BLUE)Cleaning backend artifacts...$(NC)"
	cd backend && rm -rf .pytest_cache .ruff_cache .coverage htmlcov __pycache__ **/__pycache__ *.pyc **/*.pyc
	@echo "$(GREEN)✓ Backend cleaned$(NC)"

backend-shell: ## Open Python shell with backend environment
	@echo "$(BLUE)Opening backend Python shell...$(NC)"
	cd backend && uv run python

backend-deps-update: ## Update backend dependencies
	@echo "$(BLUE)Updating backend dependencies...$(NC)"
	cd backend && uv lock --upgrade
	@echo "$(GREEN)✓ Backend dependencies updated$(NC)"

# ============================================================================
# Frontend Commands (React + TypeScript)
# ============================================================================

frontend-install: ## Install frontend dependencies
	@echo "$(BLUE)Installing frontend dependencies...$(NC)"
	@if [ -d "frontend" ]; then \
		cd frontend && npm install; \
		echo "$(GREEN)✓ Frontend dependencies installed$(NC)"; \
	else \
		echo "$(YELLOW)⚠ Frontend directory not found, skipping...$(NC)"; \
	fi

frontend-dev: ## Start frontend development server
	@echo "$(BLUE)Starting frontend server...$(NC)"
	@if [ -d "frontend" ]; then \
		cd frontend && npm run dev; \
	else \
		echo "$(YELLOW)⚠ Frontend directory not found, skipping...$(NC)"; \
	fi

frontend-lint: ## Run frontend linting (ESLint)
	@echo "$(BLUE)Running frontend linting...$(NC)"
	@if [ -d "frontend" ]; then \
		cd frontend && npm run lint; \
		echo "$(GREEN)✓ Frontend linting passed$(NC)"; \
	else \
		echo "$(YELLOW)⚠ Frontend directory not found, skipping...$(NC)"; \
	fi

frontend-lint-fix: ## Auto-fix frontend linting issues
	@echo "$(BLUE)Auto-fixing frontend linting issues...$(NC)"
	@if [ -d "frontend" ]; then \
		cd frontend && npm run lint:fix; \
		echo "$(GREEN)✓ Frontend linting auto-fixed$(NC)"; \
	else \
		echo "$(YELLOW)⚠ Frontend directory not found, skipping...$(NC)"; \
	fi

frontend-format: ## Format frontend code (Prettier)
	@echo "$(BLUE)Formatting frontend code...$(NC)"
	@if [ -d "frontend" ]; then \
		cd frontend && npm run format; \
		echo "$(GREEN)✓ Frontend code formatted$(NC)"; \
	else \
		echo "$(YELLOW)⚠ Frontend directory not found, skipping...$(NC)"; \
	fi

frontend-format-check: ## Check frontend formatting without modifying files
	@echo "$(BLUE)Checking frontend formatting...$(NC)"
	@if [ -d "frontend" ]; then \
		cd frontend && npm run format:check; \
		echo "$(GREEN)✓ Frontend formatting is correct$(NC)"; \
	else \
		echo "$(YELLOW)⚠ Frontend directory not found, skipping...$(NC)"; \
	fi

frontend-type: ## Run frontend type checking (tsc)
	@echo "$(BLUE)Running frontend type checking...$(NC)"
	@if [ -d "frontend" ]; then \
		cd frontend && npm run type-check; \
		echo "$(GREEN)✓ Frontend type checking passed$(NC)"; \
	else \
		echo "$(YELLOW)⚠ Frontend directory not found, skipping...$(NC)"; \
	fi

frontend-test: ## Run frontend tests (Vitest)
	@echo "$(BLUE)Running frontend tests...$(NC)"
	@if [ -d "frontend" ]; then \
		cd frontend && npm run test; \
		echo "$(GREEN)✓ Frontend tests passed$(NC)"; \
	else \
		echo "$(YELLOW)⚠ Frontend directory not found, skipping...$(NC)"; \
	fi

frontend-test-watch: ## Run frontend tests in watch mode
	@echo "$(BLUE)Running frontend tests in watch mode...$(NC)"
	@if [ -d "frontend" ]; then \
		cd frontend && npm run test:watch; \
	else \
		echo "$(YELLOW)⚠ Frontend directory not found, skipping...$(NC)"; \
	fi

frontend-build: ## Build frontend for production
	@echo "$(BLUE)Building frontend...$(NC)"
	@if [ -d "frontend" ]; then \
		cd frontend && npm run build; \
		echo "$(GREEN)✓ Frontend built successfully$(NC)"; \
	else \
		echo "$(YELLOW)⚠ Frontend directory not found, skipping...$(NC)"; \
	fi

frontend-preview: ## Preview frontend production build
	@echo "$(BLUE)Previewing frontend build...$(NC)"
	@if [ -d "frontend" ]; then \
		cd frontend && npm run preview; \
	else \
		echo "$(YELLOW)⚠ Frontend directory not found, skipping...$(NC)"; \
	fi

frontend-check: frontend-lint frontend-format-check frontend-type frontend-test ## Run all frontend checks

frontend-fix: frontend-lint-fix frontend-format ## Auto-fix all frontend issues

frontend-clean: ## Clean frontend build artifacts and caches
	@echo "$(BLUE)Cleaning frontend artifacts...$(NC)"
	@if [ -d "frontend" ]; then \
		cd frontend && rm -rf node_modules/.vite dist .turbo; \
		echo "$(GREEN)✓ Frontend cleaned$(NC)"; \
	else \
		echo "$(YELLOW)⚠ Frontend directory not found, skipping...$(NC)"; \
	fi

frontend-deps-update: ## Update frontend dependencies
	@echo "$(BLUE)Updating frontend dependencies...$(NC)"
	@if [ -d "frontend" ]; then \
		cd frontend && npm update; \
		echo "$(GREEN)✓ Frontend dependencies updated$(NC)"; \
	else \
		echo "$(YELLOW)⚠ Frontend directory not found, skipping...$(NC)"; \
	fi

# ============================================================================
# Docker Commands
# ============================================================================

docker-build: ## Build all Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	docker compose build
	@echo "$(GREEN)✓ Docker images built$(NC)"

docker-up: ## Start all services with Docker Compose
	@echo "$(BLUE)Starting services...$(NC)"
	docker compose up -d
	@echo "$(GREEN)✓ Services started$(NC)"
	@echo ""
	@echo "$(YELLOW)Services running:$(NC)"
	@echo "  Backend:   http://localhost:8000"
	@echo "  Postgres:  localhost:5432 (user: aide, pass: aide, db: aide)"
	@echo ""
	@echo "View logs: make docker-logs"

docker-dev: docker-up ## Start services and follow logs
	@echo "$(BLUE)Following logs (Ctrl+C to stop watching)...$(NC)"
	docker compose logs -f

docker-down: ## Stop all services
	@echo "$(BLUE)Stopping services...$(NC)"
	docker compose down
	@echo "$(GREEN)✓ Services stopped$(NC)"

docker-restart: ## Restart all services
	@echo "$(BLUE)Restarting services...$(NC)"
	docker compose restart
	@echo "$(GREEN)✓ Services restarted$(NC)"

docker-logs: ## Show logs from all services
	docker compose logs -f

docker-logs-backend: ## Show backend logs only
	docker compose logs -f backend

docker-logs-postgres: ## Show postgres logs only
	docker compose logs -f postgres

docker-ps: ## Show running containers
	@echo "$(BLUE)Running containers:$(NC)"
	@docker compose ps

docker-test: ## Run tests in Docker container
	@echo "$(BLUE)Running tests in Docker...$(NC)"
	docker compose --profile test up backend-test --build --abort-on-container-exit
	@echo "$(GREEN)✓ Tests completed$(NC)"

docker-test-watch: ## Run tests in watch mode in Docker
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	docker compose --profile test run --rm backend-test pytest-watch

docker-shell: ## Open shell in backend container
	@echo "$(BLUE)Opening shell in backend container...$(NC)"
	docker compose exec backend sh

docker-shell-test: ## Open shell in test container
	@echo "$(BLUE)Opening shell in test container...$(NC)"
	docker compose --profile test run --rm backend-test sh

docker-clean: ## Remove all containers, images, and volumes
	@echo "$(BLUE)Cleaning Docker resources...$(NC)"
	docker compose down -v --rmi all
	@echo "$(GREEN)✓ Docker resources cleaned$(NC)"

docker-prune: ## Remove all unused Docker resources
	@echo "$(RED)⚠ This will remove ALL unused Docker resources!$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to cancel...$(NC)"
	@sleep 3
	docker system prune -af --volumes
	@echo "$(GREEN)✓ Docker system pruned$(NC)"

# ============================================================================
# Database Commands
# ============================================================================

db-migrate: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(NC)"
	cd backend && uv run alembic upgrade head
	@echo "$(GREEN)✓ Migrations applied$(NC)"

db-rollback: ## Rollback last database migration
	@echo "$(BLUE)Rolling back last migration...$(NC)"
	cd backend && uv run alembic downgrade -1
	@echo "$(GREEN)✓ Migration rolled back$(NC)"

db-reset: ## Reset database (drop all tables and re-run migrations)
	@echo "$(RED)⚠ This will delete all data! Press Ctrl+C to cancel...$(NC)"
	@sleep 3
	cd backend && uv run alembic downgrade base && uv run alembic upgrade head
	@echo "$(GREEN)✓ Database reset$(NC)"

# ============================================================================
# CI/CD Commands
# ============================================================================

ci: ## Run all CI checks (same as CI pipeline)
	@echo "$(BLUE)Running CI pipeline...$(NC)"
	@$(MAKE) backend-lint
	@$(MAKE) backend-format-check
	@$(MAKE) backend-type
	@$(MAKE) backend-test
	@$(MAKE) frontend-lint
	@$(MAKE) frontend-format-check
	@$(MAKE) frontend-type
	@$(MAKE) frontend-test
	@echo "$(GREEN)✓ All CI checks passed$(NC)"

# ============================================================================
# Utility Commands
# ============================================================================

setup: ## Initial setup (install deps + setup pre-commit hooks)
	@echo "$(BLUE)Setting up AIDE development environment...$(NC)"
	@$(MAKE) install
	@echo "$(GREEN)✓ Setup complete!$(NC)"
	@echo ""
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. Copy .env.example to .env and fill in values"
	@echo "  2. Run 'make dev' to start development servers"
	@echo "  3. Run 'make check' before committing"

pre-commit: backend-lint-fix backend-format frontend-lint-fix frontend-format ## Run before committing (auto-fix issues)
	@echo "$(GREEN)✓ Ready to commit!$(NC)"

status: ## Show project status
	@echo "$(BLUE)Project Status$(NC)"
	@echo ""
	@echo "$(YELLOW)Backend:$(NC)"
	@if [ -d "backend/.venv" ]; then \
		echo "  ✓ Virtual environment exists"; \
	else \
		echo "  ✗ Virtual environment not found"; \
	fi
	@if [ -f "backend/uv.lock" ]; then \
		echo "  ✓ Dependencies locked"; \
	else \
		echo "  ✗ No lock file found"; \
	fi
	@echo ""
	@echo "$(YELLOW)Frontend:$(NC)"
	@if [ -d "frontend" ]; then \
		if [ -d "frontend/node_modules" ]; then \
			echo "  ✓ Dependencies installed"; \
		else \
			echo "  ✗ Dependencies not installed"; \
		fi; \
	else \
		echo "  ⚠ Frontend directory not found"; \
	fi

# ============================================================================
# Quick Shortcuts
# ============================================================================

lint: backend-lint frontend-lint ## Run linting for both backend and frontend
format: backend-format frontend-format ## Format code for both backend and frontend
type: backend-type frontend-type ## Run type checking for both backend and frontend

# ============================================================================
# Aliases (Short Commands)
# ============================================================================

# Backend aliases (b prefix)
bi: backend-install       ## Alias for backend-install
bd: backend-dev          ## Alias for backend-dev
bl: backend-lint         ## Alias for backend-lint
blf: backend-lint-fix    ## Alias for backend-lint-fix
bf: backend-format       ## Alias for backend-format
bfc: backend-format-check ## Alias for backend-format-check
bt: backend-test         ## Alias for backend-test
btf: backend-test-fast   ## Alias for backend-test-fast
btw: backend-test-watch  ## Alias for backend-test-watch
bty: backend-type        ## Alias for backend-type
bc: backend-check        ## Alias for backend-check
bx: backend-fix          ## Alias for backend-fix
bcl: backend-clean       ## Alias for backend-clean
bsh: backend-shell       ## Alias for backend-shell

# Frontend aliases (f prefix)
fi: frontend-install      ## Alias for frontend-install
fd: frontend-dev         ## Alias for frontend-dev
fl: frontend-lint        ## Alias for frontend-lint
flf: frontend-lint-fix   ## Alias for frontend-lint-fix
ff: frontend-format      ## Alias for frontend-format
ffc: frontend-format-check ## Alias for frontend-format-check
ft: frontend-test        ## Alias for frontend-test
ftw: frontend-test-watch ## Alias for frontend-test-watch
fty: frontend-type       ## Alias for frontend-type
fb: frontend-build       ## Alias for frontend-build
fp: frontend-preview     ## Alias for frontend-preview
fc: frontend-check       ## Alias for frontend-check
fx: frontend-fix         ## Alias for frontend-fix
fcl: frontend-clean      ## Alias for frontend-clean

# Combined aliases
i: install               ## Alias for install
d: dev                   ## Alias for dev
c: check                 ## Alias for check
x: fix                   ## Alias for fix
t: test                  ## Alias for test
cl: clean                ## Alias for clean

# Docker aliases (dk prefix)
dkb: docker-build        ## Alias for docker-build
dku: docker-up           ## Alias for docker-up
dkd: docker-down         ## Alias for docker-down
dkr: docker-restart      ## Alias for docker-restart
dkl: docker-logs         ## Alias for docker-logs
dkt: docker-test         ## Alias for docker-test
dksh: docker-shell       ## Alias for docker-shell
dkps: docker-ps          ## Alias for docker-ps
dkcl: docker-clean       ## Alias for docker-clean

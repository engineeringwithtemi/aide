# syntax=docker/dockerfile:1

# ============================================================================
# Base Stage - Common dependencies
# ============================================================================
FROM python:3.13-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_SYSTEM_PYTHON=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# ============================================================================
# Development Stage
# ============================================================================
FROM base AS development

# Install all dependencies including dev dependencies
RUN uv sync --dev

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command (can be overridden in docker-compose)
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ============================================================================
# Test Stage
# ============================================================================
FROM base AS test

# Install all dependencies including dev dependencies
RUN uv sync --dev

# Copy application code
COPY . .

# Create directory for test reports
RUN mkdir -p /app/test-reports

# Set test environment
ENV ENVIRONMENT=test \
    PYTEST_TIMEOUT=300

# Default command runs tests
CMD ["uv", "run", "pytest", "-v", "--cov=app", "--cov-report=term-missing"]

# ============================================================================
# Production Stage
# ============================================================================
FROM base AS production

# Install only production dependencies
RUN uv sync --no-dev

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production command (no reload)
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

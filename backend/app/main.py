import argparse
import os
import uuid
import time
from fastapi.responses import JSONResponse
import uvicorn
import structlog
import datetime
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from app.routes.v1 import workspaces
from contextlib import asynccontextmanager
from app.config.settings import settings
from app.config.logging import setup_logging, get_logger
from app.routes.v1.exceptions import register_exception_handlers


# Initialize logging
setup_logging(
    log_level=settings.log_level,
    log_to_file=settings.log_to_file,
    log_file_path=settings.log_file_path,
    json_format=settings.log_json,
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Enriches the app with additional state and configuration like the httpx client."""
    logger.info("Application starting up")
    # Initialize resources here (db connections, etc.)
    yield
    # Cleanup resources here
    logger.info("Application shutting down")


app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    lifespan=lifespan,
    description="Backend server for AI Driven Education (AIDE).",
)

app.add_middleware(
    CORSMiddleware,  # ty: ignore[invalid-argument-type]
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handles unexpected errors, logging them and returning a generic 500 response."""

    logger.critical(
        "Unhandled exception",
        method=request.method,
        request_url=request.url,
        error=str(exc),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected internal error occurred.",
            }
        },
    )


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    structlog.contextvars.clear_contextvars()

    request_id = str(uuid.uuid4())
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
    )

    start_time = time.perf_counter()
    logger.info("Request started")

    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    logger.info(
        "Request completed",
        status_code=response.status_code,
        duration_ms=duration_ms,
    )

    response.headers["X-Request-ID"] = request_id
    return response


app.include_router(
    workspaces.router, prefix="/v1/workspaces", tags=["workspace", "workspaces"]
)


@app.get("/")
async def get_root():
    """
    Returns the application name and the version
    """

    return {"message": settings.project_name, "version": settings.version}


@app.get("/health")
async def get_health():
    """
    Returns the health status of the application
    """
    return {
        "status": "ok",
        "timestamp": datetime.datetime.now(tz=datetime.UTC).isoformat(),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AIDE Backend Engine.")
    parser.add_argument(
        "--host", type=str, default=os.getenv("HOST", "0.0.0.0"), help="Host address"
    )
    parser.add_argument(
        "--port", type=int, default=os.getenv("PORT", 7860), help="Port number"
    )
    parser.add_argument(
        "--reload", action="store_true", default=False, help="Reload code on change"
    )

    config = parser.parse_args()

    try:
        uvicorn.run(
            "main:app",
            host=config.host,
            port=config.port,
            reload=config.reload,
            reload_excludes=[".venv"],
        )
    except KeyboardInterrupt:
        print("AIDE Backend Engine shutting down...")

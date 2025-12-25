from typing import cast
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.responses import Response
from starlette.types import ExceptionHandler

from app.config.exceptions import (
    AIDEDatabaseException,
    AIDEException,
    DatabaseConnectionException,
    DuplicateEntityException,
    EntityNotFoundException,
)

from app.config.logging import get_logger

logger = get_logger(__name__)


async def aide_exception_handler(request: Request, exc: AIDEException) -> Response:
    """Generic handler for AIDE exceptions."""
    logger.warning(f"AIDEException: {exc.message}")
    return JSONResponse(
        status_code=500,
        content={"error": exc.message, "details": exc.details},
    )


async def not_found_handler(request: Request, exc: EntityNotFoundException) -> Response:
    return JSONResponse(
        status_code=404,
        content={"error": exc.message, "details": exc.details},
    )


async def duplicate_handler(
    request: Request, exc: DuplicateEntityException
) -> Response:
    return JSONResponse(
        status_code=409,
        content={"error": exc.message, "details": exc.details},
    )


async def db_connection_handler(
    request: Request, exc: DatabaseConnectionException
) -> Response:
    logger.error("Database connection failed")
    return JSONResponse(
        status_code=503,
        content={"error": "Service temporarily unavailable"},
    )


async def db_error_handler(request: Request, exc: AIDEDatabaseException) -> Response:
    logger.error(f"Database error: {exc.message}")
    return JSONResponse(
        status_code=500,
        content={"error": "An unexpected error occurred"},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers."""
    app.add_exception_handler(
        EntityNotFoundException, cast(ExceptionHandler, not_found_handler)
    )
    app.add_exception_handler(
        DuplicateEntityException, cast(ExceptionHandler, duplicate_handler)
    )
    app.add_exception_handler(
        DatabaseConnectionException, cast(ExceptionHandler, db_connection_handler)
    )
    app.add_exception_handler(
        AIDEDatabaseException, cast(ExceptionHandler, db_error_handler)
    )
    app.add_exception_handler(
        AIDEException, cast(ExceptionHandler, aide_exception_handler)
    )

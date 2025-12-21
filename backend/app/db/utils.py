import re
from collections.abc import Callable
from functools import wraps
from typing import Any, cast

from sqlalchemy.exc import (
    IntegrityError,
    OperationalError,
    SQLAlchemyError,
)

from app.config.exceptions import (
    AIDEDatabaseException,
    DatabaseConnectionException,
    DuplicateEntityException,
)

from app.config.logging import get_logger

logger = get_logger(__name__)


def parse_integrity_error(error: IntegrityError) -> DuplicateEntityException | None:
    """Extract useful info from IntegrityError."""
    error_msg = str(error.orig)

    # PostgreSQL unique violation
    # Example: 'duplicate key value violates unique constraint "workspaces_name_key"'
    unique_match = re.search(
        r'duplicate key.*"(\w+)_(\w+)_key"',
        error_msg,
    )
    if unique_match:
        table, field = unique_match.groups()
        entity = table.rstrip("s").title()  # "workspaces" -> "Workspace"
        return DuplicateEntityException(entity=entity, field=field, value="<unknown>")

    # PostgreSQL FK violation
    fk_match = re.search(
        r'violates foreign key constraint.*"(\w+)"',
        error_msg,
    )
    if fk_match:
        return None  # Handle FK errors differently if needed

    return None


def db_exception_handler[Func: Callable[..., Any]](func: Func) -> Func:
    """Decorator to handle SQLAlchemy exceptions."""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)

        except IntegrityError as e:
            logger.warning(f"Integrity error in {func.__name__}: {e}")
            parsed = parse_integrity_error(e)
            if parsed:
                raise parsed from e
            raise AIDEDatabaseException(message="Data integrity error") from e

        except OperationalError as e:
            logger.error(f"Database connection error: {e}")
            raise DatabaseConnectionException() from e

        except SQLAlchemyError as e:
            logger.error(f"Database error in {func.__name__}: {e}")
            raise AIDEDatabaseException(message="Database operation failed") from e

    return cast("Func", wrapper)
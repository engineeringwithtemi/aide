from typing import Any


class AIDEException(Exception):
    """Base exception for all AIDE errors."""

    def __init__(self, message: str, details: Any = None):
        self.message = message
        self.details = details
        super().__init__(message)


class AIDEDatabaseException(AIDEException):
    """Base database exception."""


class AIProviderException(AIDEException):
    """Base ai provider exceptions"""


class EntityNotFoundException(AIDEDatabaseException):
    """Raised when entity not found."""

    def __init__(self, entity: str, entity_id: Any):
        super().__init__(
            message=f"{entity} not found",
            details={"entity": entity, "id": str(entity_id)},
        )


class DuplicateEntityException(AIDEDatabaseException):
    """Raised on unique constraint violation."""

    def __init__(self, entity: str, field: str, value: Any):
        super().__init__(
            message=f"{entity} with {field}='{value}' already exists",
            details={"entity": entity, "field": field, "value": value},
        )


class DatabaseConnectionException(AIDEDatabaseException):
    """Raised when database is unreachable."""

    def __init__(self):
        super().__init__(message="Database connection failed")


class DatabaseTransactionException(AIDEDatabaseException):
    """Raised on transaction failures."""

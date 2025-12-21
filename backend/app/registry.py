"""Central registry for source and lab types.

This module provides functions to discover and instantiate registered
source and lab types without modifying core code.
"""

from typing import Dict, Type
from app.config.logging import get_logger
from app.sources.base import Source
from typing import List

logger = get_logger(__name__)

# ─────────────────────────────────────────────
# SOURCE REGISTRY
# ─────────────────────────────────────────────

# Global registry mapping source type identifiers to Source classes
# Example: {"pdf": PDFSource, "github": GitHubSource}
#
# This enables dynamic source type discovery and instantiation without
# modifying core code when adding new source types.
source_registry: Dict[str, Type[Source]] = {}


def register_source(cls: Type[Source]) -> Type[Source]:
    """Decorator to register a source type in the global registry.

    This decorator should be applied to all concrete Source implementations
    to make them discoverable by the system. The source type is extracted
    from the class's source_type property.

    Args:
        cls: Source class to register

    Returns:
        The same class (allows use as decorator)

    Example:
        @register_source
        class PDFSource(Source):
            source_type = "pdf"
            ...

    Note:
        Registration happens at import time. Ensure all source modules are
        imported before attempting to use the registry (e.g., in __init__.py).
    """
    source_registry[cls.source_type] = cls
    logger.info(
        "Registered source type", source_type=cls.source_type, source_class=cls.__name__
    )
    return cls


def get_source_class(source_type: str) -> Type[Source]:
    """Get Source class by type identifier.

    Args:
        source_type: Type identifier (e.g., "pdf", "github")

    Returns:
        Source class

    Raises:
        KeyError: If source type not registered
    """
    if source_type not in source_registry:
        raise KeyError(
            f"Unknown source type: {source_type}. Available: {list_source_types()}"
        )
    return source_registry[source_type]


# def get_lab_class(lab_type: str) -> Type[Lab]:
#     """Get Lab class by type identifier.

#     Args:
#         lab_type: Type identifier (e.g., "code_lab", "flashcard_lab")

#     Returns:
#         Lab class

#     Raises:
#         KeyError: If lab type not registered
#     """
#     if lab_type not in lab_registry:
#         raise KeyError(f"Unknown lab type: {lab_type}. "
#                       f"Available: {list_lab_types()}")
#     return lab_registry[lab_type]


def list_source_types() -> List[str]:
    """List all registered source types.

    Returns:
        List of source type identifiers
    """
    return list(source_registry.keys())


# def list_lab_types() -> List[str]:
#     """List all registered lab types.

#     Returns:
#         List of lab type identifiers
#     """
#     return list(lab_registry.keys())


# Convenience functions for API endpoints


def instantiate_source(source_type: str, **kwargs) -> Source:
    """Create a source instance by type.

    Args:
        source_type: Type identifier
        **kwargs: Arguments for source constructor

    Returns:
        Source instance
    """
    source_class = get_source_class(source_type)
    return source_class(**kwargs)


# def instantiate_lab(lab_type: str, **kwargs) -> Lab:
#     """Create a lab instance by type.

#     Args:
#         lab_type: Type identifier
#         **kwargs: Arguments for lab constructor

#     Returns:
#         Lab instance
#     """
#     lab_class = get_lab_class(lab_type)
#     return lab_class(**kwargs)

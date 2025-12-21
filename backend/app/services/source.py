"""Service layer for managing sources.

This module provides the business logic for source operations,
interacting with the SourceRepository for database access.
"""  # Module-level docstring

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.tables import Source
from app.db.repositories import SourceRepository
from app.config.schemas import SourceCreate, SourceUpdate
from app.config.logging import get_logger
from app.config.exceptions import EntityNotFoundException

logger = get_logger(__name__)


class SourceService:
    """Manages business logic for source-related operations."""

    def __init__(self, db: AsyncSession):
        """Initializes the SourceService with a database session.

        Args:
            db: The database session.
        """
        self.db = db
        self.source_repo = SourceRepository(db)

    async def create_source(self, data: SourceCreate) -> Source:
        """Creates a new source.

        Args:
            data: The data for creating the source.

        Returns:
            The newly created Source object.
        """
        logger.info(
            "Creating source",
            source_type=data.type,
            workspace_id=str(data.workspace_id),
        )
        source = Source(**data.model_dump())
        await self.source_repo.add(source)
        await self.db.commit()
        await self.db.refresh(source)
        logger.info("Source created successfully", source_id=str(source.id))
        return source

    async def get_source(self, source_id: UUID) -> Source:
        """Fetches a single source by its ID.

        Args:
            source_id: The unique identifier of the source.

        Returns:
            The Source object.

        Raises:
            EntityNotFoundException: If the source with the given ID is not found.
        """
        logger.debug("Fetching source", source_id=str(source_id))
        source = await self.source_repo.get_by_id(source_id)
        if not source:
            logger.warning("Source not found", source_id=str(source_id))
            raise EntityNotFoundException(entity="Source", entity_id=source_id)
        return source

    async def list_sources(self, limit: int = 100, offset: int = 0) -> list[Source]:
        """Lists all sources with pagination.

        Args:
            limit: The maximum number of sources to return.
            offset: The number of sources to skip.

        Returns:
            A list of Source objects.
        """
        logger.debug("Listing sources", limit=limit, offset=offset)
        sources = await self.source_repo.get_all(limit, offset)
        logger.debug("Retrieved sources", count=len(sources))
        return sources

    async def update_source(self, source_id: UUID, data: SourceUpdate) -> Source:
        """Updates an existing source.

        Args:
            source_id: The unique identifier of the source to update.
            data: The update data for the source.

        Returns:
            The updated Source object.

        Raises:
            EntityNotFoundException: If the source with the given ID is not found.
        """
        logger.info("Updating source", source_id=str(source_id))
        source = await self.get_source(source_id)
        update_data = data.model_dump(exclude_unset=True)
        logger.debug(
            "Update data", source_id=str(source_id), fields=list(update_data.keys())
        )

        await self.source_repo.update(source, update_data)
        await self.db.commit()
        await self.db.refresh(source)
        logger.info("Source updated successfully", source_id=str(source_id))
        return source

    async def delete_source(self, source_id: UUID) -> None:
        """Deletes a source by its ID.

        Args:
            source_id: The unique identifier of the source to delete.

        Raises:
            EntityNotFoundException: If the source with the given ID is not found.
        """
        logger.info("Deleting source", source_id=str(source_id))
        source = await self.get_source(source_id)
        await self.source_repo.delete(source)
        await self.db.commit()
        logger.info("Source deleted successfully", source_id=str(source.id))

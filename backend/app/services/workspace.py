"""Service layer for managing workspaces.

This module provides the business logic for workspace operations,
interacting with the WorkspaceRepository for database access.
""" # Module-level docstring

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.tables import Workspace
from app.db.repositories import WorkspaceRepository
from app.config.schemas import WorkspaceCreate, WorkspaceUpdate
from app.config.logging import get_logger
from app.config.exceptions import EntityNotFoundException

logger = get_logger(__name__)


class WorkspaceService:
    """Manages business logic for workspace-related operations."""

    def __init__(self, db: AsyncSession):
        """Initializes the WorkspaceService with a database session.

        Args:
            db: The asynchronous database session.
        """
        # DB session for transaction management (commit/rollback)
        # All queries go through repositories
        self.db = db
        self.workspace_repo = WorkspaceRepository(db)

    # -------- Workspace Operations --------

    async def create_workspace(self, data: WorkspaceCreate) -> Workspace:
        """Creates a new workspace.

        Args:
            data: The data for creating the workspace.

        Returns:
            The newly created Workspace object.
        """
        logger.info("Creating workspace", workspace_name=data.name)
        workspace = Workspace(**data.model_dump())
        await self.workspace_repo.add(workspace)
        await self.db.commit()
        await self.db.refresh(workspace)
        logger.info("Workspace created successfully", workspace_id=str(workspace.id))
        return workspace

    async def get_workspace(self, workspace_id: UUID) -> Workspace:
        """Fetches a single workspace by its ID.

        Args:
            workspace_id: The unique identifier of the workspace.

        Returns:
            The Workspace object.

        Raises:
            EntityNotFoundException: If the workspace with the given ID is not found.
        """
        logger.debug("Fetching workspace", workspace_id=str(workspace_id))
        workspace = await self.workspace_repo.get_by_id(workspace_id)
        if not workspace:
            logger.warning("Workspace not found", workspace_id=str(workspace_id))
            raise EntityNotFoundException(entity="Workspace", entity_id=workspace_id)
        return workspace

    async def list_workspaces(self, limit: int = 100, offset: int = 0) -> list[Workspace]:
        """Lists all workspaces with pagination.

        Args:
            limit: The maximum number of workspaces to return.
            offset: The number of workspaces to skip.

        Returns:
            A list of Workspace objects.
        """
        logger.debug("Listing workspaces", limit=limit, offset=offset)
        workspaces = await self.workspace_repo.get_all(limit, offset)
        logger.debug("Retrieved workspaces", count=len(workspaces))
        return workspaces

    async def update_workspace(self, workspace_id: UUID, data: WorkspaceUpdate) -> Workspace:
        """Updates an existing workspace.

        Args:
            workspace_id: The unique identifier of the workspace to update.
            data: The update data for the workspace.

        Returns:
            The updated Workspace object.

        Raises:
            EntityNotFoundException: If the workspace with the given ID is not found.
        """
        logger.info("Updating workspace", workspace_id=str(workspace_id))
        workspace = await self.get_workspace(workspace_id)
        update_data = data.model_dump(exclude_unset=True)
        logger.debug("Update data", workspace_id=str(workspace_id), fields=list(update_data.keys()))

        await self.workspace_repo.update(workspace, update_data)
        await self.db.commit()
        await self.db.refresh(workspace)
        logger.info("Workspace updated successfully", workspace_id=str(workspace.id))
        return workspace

    async def delete_workspace(self, workspace_id: UUID) -> None:
        """Deletes a workspace by its ID.

        Args:
            workspace_id: The unique identifier of the workspace to delete.

        Raises:
            EntityNotFoundException: If the workspace with the given ID is not found.
        """
        logger.info("Deleting workspace", workspace_id=str(workspace_id))
        workspace = await self.get_workspace(workspace_id)
        await self.workspace_repo.delete(workspace)
        await self.db.commit()
        logger.info("Workspace deleted successfully", workspace_id=str(workspace.id))

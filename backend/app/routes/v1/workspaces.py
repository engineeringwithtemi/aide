"""Workspace management API endpoints."""

from fastapi import APIRouter
from app.config.logging import get_logger
from app.config.schemas import WorkspaceCreate, WorkspaceRead, WorkspaceUpdate
from app.config.dependencies import WorkspaceSvc
from uuid import UUID

router = APIRouter()

logger = get_logger(__name__)


@router.post("", status_code=201, response_model=WorkspaceRead)
async def create_workspace(request: WorkspaceCreate, workspace_svc: WorkspaceSvc):
    """Create a new workspace.

    Body:
        - name: str (workspace name)

    Returns:
        201: WorkspaceRead with new workspace ID and metadata
    """
    workspace = await workspace_svc.create_workspace(request)
    return WorkspaceRead.model_validate(workspace)


@router.get("", response_model=list[WorkspaceRead])
async def list_workspaces(
    workspace_svc: WorkspaceSvc, limit: int = 100, offset: int = 0
):
    """List all workspaces with pagination.

    Query Parameters:
        - limit: int (default: 100, max number of workspaces to return)
        - offset: int (default: 0, number of workspaces to skip)

    Returns:
        200: List of WorkspaceRead objects
    """
    workspaces = await workspace_svc.list_workspaces(limit=limit, offset=offset)
    return [WorkspaceRead.model_validate(ws) for ws in workspaces]


@router.get("/{workspace_id}", response_model=WorkspaceRead)
async def get_workspace(workspace_id: UUID, workspace_svc: WorkspaceSvc):
    """Get a specific workspace by ID.

    Path Parameters:
        - workspace_id: UUID

    Returns:
        200: WorkspaceRead with workspace details
        404: Workspace not found
    """
    workspace = await workspace_svc.get_workspace(workspace_id)
    return WorkspaceRead.model_validate(workspace)


@router.patch("/{workspace_id}", response_model=WorkspaceRead)
async def update_workspace(
    workspace_id: UUID, request: WorkspaceUpdate, workspace_svc: WorkspaceSvc
):
    """Update an existing workspace.

    Path Parameters:
        - workspace_id: UUID

    Body:
        - name: Optional[str] (new workspace name)

    Returns:
        200: WorkspaceRead with updated workspace details
        404: Workspace not found
    """
    workspace = await workspace_svc.update_workspace(workspace_id, request)
    return WorkspaceRead.model_validate(workspace)


@router.delete("/{workspace_id}", status_code=204)
async def delete_workspace(workspace_id: UUID, workspace_svc: WorkspaceSvc):
    """Delete a workspace.

    This will cascade delete all associated:
    - Sources
    - Labs
    - Chat messages
    - Edges
    - Settings

    Path Parameters:
        - workspace_id: UUID

    Returns:
        204: No content (success)
        404: Workspace not found
    """
    await workspace_svc.delete_workspace(workspace_id)

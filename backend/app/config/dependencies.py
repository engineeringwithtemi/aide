from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection import get_db
from app.services.workspace import WorkspaceService
from app.services.source import SourceService
from app.config.logging import get_logger
from app.services.supabase import SupabaseService

logger = get_logger(__name__)


async def get_workspace_service(db: AsyncSession = Depends(get_db)) -> WorkspaceService:
    logger.debug("Dependency injection", service="WorkspaceService")
    return WorkspaceService(db)


async def get_source_service(db: AsyncSession = Depends(get_db)) -> SourceService:
    logger.debug("Dependency injection", service="SourceService")
    return SourceService(db)

async def get_supabase_service(request:Request) -> SupabaseService:
    logger.debug("Dependency injection", service="StorageService")
    return request.app.state.supabase_service


# Type aliases for cleaner route signatures
DbSession = Annotated[AsyncSession, Depends(get_db)]
WorkspaceSvc = Annotated[WorkspaceService, Depends(get_workspace_service)]
SourceSvc = Annotated[SourceService, Depends(get_source_service)]
SupabaseSvc = Annotated[SupabaseService, Depends(get_supabase_service)]
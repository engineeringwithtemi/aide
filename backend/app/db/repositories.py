from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import select
from app.db.tables import Base, Workspace, Source, Lab
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.utils import db_exception_handler
from app.config.logging import get_logger

logger = get_logger(__name__)

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations."""

    def __init__(self, model: type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    @db_exception_handler
    async def get_by_id(self, id: UUID) -> ModelType | None:
        logger.debug("Repository get_by_id", model=self.model.__name__, id=str(id))
        return await self.db.get(self.model, id)

    @db_exception_handler
    async def get_all(self, limit: int = 100, offset: int = 0) -> list[ModelType]:
        logger.debug(
            "Repository get_all", model=self.model.__name__, limit=limit, offset=offset
        )
        stmt = select(self.model).limit(limit).offset(offset)
        result = await self.db.scalars(stmt)
        return list(result)

    @db_exception_handler
    async def add(self, entity: ModelType) -> ModelType:
        logger.debug("Repository add", model=self.model.__name__)
        self.db.add(entity)
        await self.db.flush()
        return entity

    @db_exception_handler
    async def update(self, entity: ModelType, data: dict) -> ModelType:
        logger.debug(
            "Repository update", model=self.model.__name__, fields=list(data.keys())
        )
        for key, value in data.items():
            setattr(entity, key, value)
        await self.db.flush()
        return entity

    @db_exception_handler
    async def delete(self, entity: ModelType) -> None:
        logger.debug("Repository delete", model=self.model.__name__)
        await self.db.delete(entity)
        await self.db.flush()


class WorkspaceRepository(BaseRepository[Workspace]):
    def __init__(self, db: AsyncSession):
        super().__init__(Workspace, db)


class SourceRepository(BaseRepository[Source]):
    def __init__(self, db: AsyncSession):
        super().__init__(Source, db)

    @db_exception_handler
    async def get_by_workspace(self, workspace_id: UUID) -> list[Source]:
        logger.debug(
            "Repository get_by_workspace",
            model="Source",
            workspace_id=str(workspace_id),
        )
        stmt = select(Source).where(Source.workspace_id == workspace_id)
        results = await self.db.scalars(stmt)
        results_list = list(results)
        logger.debug(
            "Repository get_by_workspace result",
            model="Source",
            workspace_id=str(workspace_id),
            count=len(results_list),
        )
        return results_list


class LabRepository(BaseRepository[Lab]):
    def __init__(self, db: AsyncSession):
        super().__init__(Lab, db)

    @db_exception_handler
    async def get_by_workspace(self, workspace_id: UUID) -> list[Lab]:
        logger.debug(
            "Repository get_by_workspace", model="Lab", workspace_id=str(workspace_id)
        )
        stmt = select(Lab).where(Lab.workspace_id == workspace_id)
        results = await self.db.scalars(stmt)
        results_list = list(results)
        logger.debug(
            "Repository get_by_workspace result",
            model="Lab",
            workspace_id=str(workspace_id),
            count=len(results_list),
        )
        return results_list

    @db_exception_handler
    async def get_by_source(self, source_id: UUID) -> list[Lab]:
        logger.debug("Repository get_by_source", model="Lab", source_id=str(source_id))
        stmt = select(Lab).where(Lab.source_id == source_id)

        results = await self.db.scalars(stmt)
        results_list = list(results)
        logger.debug(
            "Repository get_by_source result",
            model="Lab",
            source_id=str(source_id),
            count=len(results_list),
        )
        return results_list

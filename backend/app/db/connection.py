from app.config.settings import settings
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

engine = create_async_engine(
    settings.database_url, pool_pre_ping=True, pool_recycle=300, echo=settings.debug
)

AsyncSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=True, bind=engine, class_=AsyncSession
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Database dependency for FastAPI.

    Creates a database session for each request and ensures it's properly closed.
    Includes proper transaction management and error handling.

    Example:
        @app.get("/workspaces/")
        def get_workspaces(db: Session = Depends(get_db)):
            return db.query(Workspace).all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise

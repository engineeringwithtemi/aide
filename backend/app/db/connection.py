from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings
from functools import cache
from app.config.schemas import AIDEDatabaseException
from sqlalchemy.orm import Session
from typing import Generator
from collections.abc import Callable
from functools import wraps
from typing import Any, cast

engine = create_engine(
    settings.database_url, pool_pre_ping=True, pool_recycle=300, echo=settings.debug
)

SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)


@cache
def get_db() -> Generator[Session, None, None]:
    """
    Database dependency for FastAPI.

    Creates a database session for each request and ensures it's properly closed.
    Includes proper transaction management and error handling.

    Example:
        @app.get("/workspaces/")
        def get_workspaces(db: Session = Depends(get_db)):
            return db.query(Workspace).all()
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        # Rollback the transaction on any exception
        db.rollback()
        raise
    finally:
        # Always close the session
        db.close()


@cache
def get_db_transactional() -> Generator[Session, None, None]:
    """
    Database dependency for FastAPI with automatic transaction management.

    Automatically commits successful operations and rolls back on exceptions.
    Use this for write operations where you want automatic transaction handling.

    Example:
        @app.post("/workspaces/")
        def create_workspace(workspace_data: Workspace, db: Session = Depends(get_db_transactional)):
            workspace = Workspace(**workspace_data.dict())
            db.add(workspace)
            # Transaction will be automatically committed
            return workspace
    """
    db = SessionLocal()
    try:
        yield db
        # Commit the transaction if no exceptions occurred
        db.commit()
    except Exception:
        # Rollback the transaction on any exception
        db.rollback()
        raise
    finally:
        # Always close the session
        db.close()


def aidedb_exception_wrapper[Func: Callable[..., Any]](func: Func) -> Func:
    """Wrapper used to forward re-throw exceptions as AIDEDatabaseException."""

    @wraps(func)
    async def _decorated(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except Exception as exception:
            get_db.cache_clear()
            get_db_transactional.cache_clear()
            msg = f"AIDEDatabaseException error: {exception}"
            raise AIDEDatabaseException(msg) from exception

    return cast("Func", _decorated)

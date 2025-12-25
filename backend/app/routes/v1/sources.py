"""Source management API endpoints"""

from fastapi import UploadFile, APIRouter, HTTPException
from app.config.logging import get_logger
from app.config.schemas import SourceCreate, SourceRead, SourceUpdate
from app.config.dependencies import SourceSvc, SupabaseSvc
from uuid import UUID
from app.registry import instantiate_source, get_source_class
import tempfile
import shutil
import os

from app.sources import _discover_sources

_discover_sources()

router = APIRouter(prefix="/sources", tags=["sources", "source"])

logger = get_logger(__name__)


@router.post("", status_code=201, response_model=SourceRead)
async def create_source(request: SourceCreate, source_svc: SourceSvc):
    """Create empty source record.

    Body:
        - workspace_id: UUID
        - type: "pdf" (only type supported in MVP)
        - title: string

    Returns:
        201: SourceResponse with new source ID
    """
    db_source = await source_svc.create_source(request)

    return SourceRead.model_validate(db_source)


@router.post("/{id}/upload")
async def upload_source(
    id: UUID, file: UploadFile, source_svc: SourceSvc, supabase_svc: SupabaseSvc
):
    if file.content_type != "application/pdf":
        raise HTTPException(400, "Only PDF files are supported")

    db_source = await source_svc.get_source(id)

    if db_source.storage_path:
        raise HTTPException(
            409, "Source content already uploaded. Delete and re-create to replace."
        )

    file.file.seek(0, 2)  # Seek to end
    size = file.file.tell()
    file.file.seek(0)  # Reset

    if size > 50 * 1024 * 1024:  # 50MB
        raise HTTPException(413, "File too large (max 50MB)")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_path = temp_file.name

    try:
        source_instance = instantiate_source(
            db_source.type,
            id=db_source.id,
            workspace_id=db_source.workspace_id,
            title=db_source.title,
            supabase_service=supabase_svc,
            source_service=source_svc,
        )
        source_metadata = await source_instance.setup({"file_path": temp_path})

        await source_svc.update_source(
            id,
            SourceUpdate(
                storage_path=source_instance.storage_path,
                meta_data=source_metadata.metadata,
                cache_id=source_instance.cache_id,
                cache_expires_at=source_instance.cache_expires_at,
            ),
        )
        return source_instance.get_view_data()
    except Exception as e:
        logger.error(f"Source upload failed: {e}", source_id=str(id))
        raise HTTPException(500, f"Failed to process PDF: {str(e)}")
    finally:
        os.unlink(temp_path)


@router.get("/{source_id}")
async def get_source(source_id: UUID, source_svc: SourceSvc):
    """Get source view data.

    Returns:
        200: SourceRead with view data
        404: Source not found (raised by service)
    """
    db_source = await source_svc.get_source(source_id)

    source_class = get_source_class(db_source.type)
    source = await source_class.setup_from_db(db_source)

    return source.get_view_data()


@router.patch("/{source_id}")
async def update_source(source_id: UUID, request: SourceUpdate, source_svc: SourceSvc):
    """Update source (e.g., change current chapter).
    Body:
        - current_chapter_id: Optional[str]
        - Any source-specific fields
    """
    db_source = await source_svc.update_source(source_id, request)

    return SourceRead.model_validate(db_source)


@router.delete("/{source_id}", status_code=204)
async def delete_source(
    source_id: UUID, source_svc: SourceSvc, supabase_svc: SupabaseSvc
):
    """Delete source and associated file.

    Cascade deletes labs linked to this source.
    404 raised by service if source not found.
    """
    source_db = await source_svc.get_source(source_id)

    # Delete from storage
    if source_db.storage_path:
        await supabase_svc.delete_files([source_db.storage_path])

    # Delete from DB (cascade)
    await source_svc.delete_source(source_id)

"""Source management API endpoints"""

from fastapi import UploadFile, File, APIRouter, HTTPException, Depends
from app.config.logging import get_logger
from app.config.schemas import SourceCreate, SourceRead, SourceUpdate
from app.config.dependencies import SourceSvc, SupabaseSvc
from uuid import UUID
from app.registry import instantiate_source
import tempfile
import shutil
import os
router = APIRouter(prefix="/sources", tags=["sources", "source"])

logger = get_logger(__name__)

@router.post("", status_code=201, response_model=SourceRead)
async def create_source(request:SourceCreate, source_svc: SourceSvc):
    """Create empty source record.

    Body:
        - workspace_id: UUID
        - type: "pdf" (only type supported in MVP)
        - title: string

    Returns:
        201: SourceResponse with new source ID
    """
    db_source = await source_svc.create_source(request)

    return SourceRead(**db_source)

@router.post("/{id}/upload")
async def upload_source(id: UUID, file: UploadFile, source_svc: SourceSvc, supabase_svc: SupabaseSvc):
    db_source = await source_svc.get_source(id)


    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_path = temp_file.name

    try:
        source_instance = instantiate_source(db_source.type, id=db_source.id,         
                                             workspace_id=db_source.workspace_id,
                        title=db_source.title,
                        supabase_service=supabase_svc,
                        source_service=source_svc
        )
        source_metadata = await source_instance.setup({"file_path": temp_path})

        await source_svc.update_source(id, SourceUpdate(
            storage_path=source_instance.storage_path,
            meta_data=source_metadata.metadata,
            cache_id = source_instance.cache_id,
            cache_expires_at= source_instance.cache_expires_at
        ))
        return source_instance.get_view_data()
    finally:
        os.unlink(temp_path)

from supabase import AsyncClient
from typing import List
from app.config.logging import get_logger

logger = get_logger(__name__)


class SupabaseService:
    def __init__(self, client: AsyncClient):
        self.client = client
        self.bucket = "uploads"
        self._bucket_ensured = False

    async def _ensure_bucket_exists(self):
        """Ensure the storage bucket exists.

        Note: The bucket should be created via Supabase migrations.
        This just verifies it exists.
        """
        if self._bucket_ensured:
            return

        try:
            # Try to get bucket info to check if it exists
            await self.client.storage.get_bucket(self.bucket)
            logger.info("Storage bucket exists", bucket=self.bucket)
            self._bucket_ensured = True
        except Exception as e:
            logger.error(
                "Storage bucket not found. Create it via Supabase migrations.",
                bucket=self.bucket,
                error=str(e),
            )
            raise Exception(
                f"Storage bucket '{self.bucket}' does not exist. Run: supabase db reset"
            )

    async def upload_file(self, file_path) -> str:
        await self._ensure_bucket_exists()

        with open(file_path, "rb") as f:
            response = await self.client.storage.from_(self.bucket).upload(
                file=f,
                path=f"public/{file_path}",
                file_options={"cache-control": "3600", "upsert": "true"},
            )
            return response.full_path

    async def delete_files(self, file_paths: List[str]):
        await self.client.storage.from_(self.bucket).remove(file_paths)

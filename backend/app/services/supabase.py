from supabase import AsyncClient


class SupabaseService:
    def __init__(self, client:AsyncClient):
        self.client = client
        self.bucket = "uploads"

    async def upload_file(self, file_path)-> str:
        with open(self.file_path, "rb") as f:
            response = (
                await self.client.storage
                .from_(self.bucket)
                .upload(
                    file=f,
                    path=f"public/{file_path}",
                    file_options={"cache-control": "3600", "upsert": "true"}
                )
            )
            return response.full_path
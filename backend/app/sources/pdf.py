from app.registry import register_source, LAB_REGISTRY
from app.sources.base import Source
from app.config.schemas import Chapter, SourceMetadata
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from app.services.pdf_parser import extract_chapters
from app.services.supabase import SupabaseService
from app.services.source import SourceService
from app.db.tables import Source as SourceModel


@register_source
class PDFSource(Source):
    """PDF document source implementation.

    Handles PDF parsing, chapter extraction, and content caching.
    """

    source_type = "pdf"

    def __init__(
        self,
        id: UUID,
        workspace_id: UUID,
        title: str,
        supabase_service: Optional[SupabaseService] = None,
        cache_id: Optional[str] = None,
        cache_expires_at: Optional[datetime] = None,
        source_service: Optional[SourceService] = None,
    ):
        # Pass required args to parent, including the type
        super().__init__(
            id, workspace_id, "pdf", title, cache_id, cache_expires_at, source_service
        )
        self.supabase_service = supabase_service
        # Internal state - populated by setup() or during hydration
        self.chapters: List[Chapter] = []
        self.current_chapter_id: Optional[str] = None
        self.storage_path: str = ""

    async def setup(self, config: Dict[str, Any]) -> SourceMetadata:
        """Parse PDF and create initial cache.

        Args:
            config: Must contain:
                - file_path: Path to uploaded PDF file
                - OR file_content: bytes of PDF content

        Returns:
            SourceMetadata with chapters list
        """
        # 1. Get PDF content
        file_path = config.get("file_path")
        file_content = config.get("file_content")

        # 2. Parse PDF to extract chapters
        self.chapters = await extract_chapters(file_content or file_path)

        # 3. Upload to storage
        if self.supabase_service:
            self.storage_path = await self.supabase_service.upload_file(file_path)

        # 4. Create cache (automatic via abstract class)
        await self.get_cache_id()

        # 5. Set initial chapter
        if self.chapters:
            self.current_chapter_id = self.chapters[0].id

        return SourceMetadata(
            title=self.title,
            metadata={
                "chapters": [
                    {"id": ch.id, "title": ch.title, "start_page": ch.start_page}
                    for ch in self.chapters
                ]
            },
        )

    async def get_full_content(self) -> str:
        """Return all chapters for caching."""
        content_parts = []
        for chapter in self.chapters:
            content_parts.append(
                f"=== {chapter.title} (Pages {chapter.start_page}-{chapter.end_page}) ===\n\n{chapter.text}"
            )
        return "\n\n".join(content_parts)

    async def get_content_for_generation(self, context: Dict[str, Any]) -> str:
        """Get specific chapter text for lab generation."""
        chapter_id = context.get("chapter_id")
        if not chapter_id:
            raise ValueError("chapter_id required in context")

        chapter = next((ch for ch in self.chapters if ch.id == chapter_id), None)
        if not chapter:
            raise ValueError(f"Chapter not found: {chapter_id}")

        return chapter.text

    def get_current_context(self) -> Dict[str, Any]:
        """Get current chapter info."""
        if not self.current_chapter_id:
            return {}

        chapter = next(
            (ch for ch in self.chapters if ch.id == self.current_chapter_id), None
        )
        if not chapter:
            return {}

        return {
            "reference": chapter.title,
            "page": chapter.start_page,
            "chapter_id": chapter.id,
        }

    def get_available_lab_types(self) -> List[str]:
        """PDF can generate code labs (MVP)."""
        return [
            lab_type
            for lab_type, lab_class in LAB_REGISTRY.items()
            if self.source_type in lab_class.supported_sources
        ]

    def get_actions(self) -> List[Dict[str, Any]]:
        """Automatically generate actions from compatible labs."""
        actions = []

        for lab_type, lab_class in LAB_REGISTRY.items():
            if self.source_type in lab_class.supported_sources:
                action = lab_class.get_action_metadata()

                if hasattr(self, "_enhance_action_config"):
                    action = self._enhance_action_config(action)

                actions.append(action)

        return actions

    def _enhance_action_config(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Add PDF-specific config like chapter selection."""
        # Add chapter_id to config_schema for PDF sources
        if "config_schema" not in action:
            action["config_schema"] = {"type": "object", "properties": {}}

        config_schema = action["config_schema"]
        if isinstance(config_schema, dict):
            if "properties" not in config_schema:
                config_schema["properties"] = {}

            properties = config_schema.get("properties")
            if isinstance(properties, dict):
                properties["chapter_id"] = {
                    "type": "string",
                    "description": "Chapter to generate from",
                }

            required = config_schema.setdefault("required", [])
            if isinstance(required, list):
                required.append("chapter_id")

        return action

    def get_chat_context(self) -> Dict[str, Any]:
        """Context for chat @mentions."""
        return {
            "id": str(self.id),
            "type": self.source_type,
            "title": self.title,
            "cache_id": self.cache_id,
            "context": self.get_current_context(),
            "total_chapters": len(self.chapters),
        }

    def get_view_data(self) -> Dict[str, Any]:
        """Data for frontend PDF viewer."""
        return {
            "type": "pdf",
            "title": self.title,
            "storage_url": self.storage_path,
            "chapters": [
                {
                    "id": ch.id,
                    "title": ch.title,
                    "start_page": ch.start_page,
                    "end_page": ch.end_page,
                }
                for ch in self.chapters
            ],
            "current_chapter_id": self.current_chapter_id,
            "total_pages": self.chapters[-1].end_page if self.chapters else 0,
        }

    @classmethod
    async def setup_from_db(cls, source: SourceModel):
        instance = cls(
            id=source.id,
            workspace_id=source.workspace_id,
            title=source.title,
            cache_id=source.cache_id,
            cache_expires_at=source.cache_expires_at,
        )

        instance.storage_path = source.storage_path or ""

        if source.meta_data:
            # Extract chapters list from metadata dict
            chapters_data = source.meta_data.get("chapters", [])
            instance.chapters = [
                Chapter(
                    id=ch["id"],
                    title=ch["title"],
                    start_page=ch["start_page"],
                    end_page=ch.get(
                        "end_page", ch["start_page"]
                    ),  # Handle missing end_page
                    text="",
                )
                for ch in chapters_data
            ]

            # Set current chapter if available
            if instance.chapters:
                instance.current_chapter_id = instance.chapters[0].id

        return instance

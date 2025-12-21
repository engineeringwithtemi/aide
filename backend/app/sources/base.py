from uuid import UUID
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Type
from app.services.ai import ai_provider, aiprovider_exception_wrapper
from app.config.schemas import SourceMetadata, SourceUpdate
from app.config.dependencies import SourceSvc
from app.config.logging import get_logger

logger = get_logger()

class Source(ABC):
    """Base class all sources must implement"""

    def __init__(
        self,
        id: UUID,
        workspace_id: UUID,
        type: str,
        title: str,
        cache_id: Optional[str] = None,
        cache_expires_at: Optional[datetime] = None,
        source_service: Optional[SourceSvc] = None  
    ):
        self.id = id
        self.workspace_id = workspace_id
        self.type = type
        self.title = title
        self.cache_id = cache_id
        self.cache_expires_at = cache_expires_at
        self._source_service = source_service  

        logger.info("Initialized Source base class", source_class=self.__class__.__name__, source_id=str(self.id))
    @property
    @abstractmethod
    def source_type(self) -> str:
        """Unique identifier for this source type (e.g., 'pdf', 'github')"""
        pass

    @abstractmethod
    async def setup(self, config: Dict[str, Any]) -> SourceMetadata:
        """
        Called when source is first added/configured.
        For PDF: parse chapters, cache with AI
        For GitHub: clone repo, index files
        """
        pass

    @abstractmethod
    async def get_full_content(self) -> str:
        """
        Returns ALL content for this source to be cached.
        - PDF: entire book text with chapter markers
        - GitHub: all file contents concatenated
        - Video: full transcript

        This is called by the abstract class when caching.
        Concrete classes just return the content.
        """
        pass

    @abstractmethod
    async def get_content_for_generation(self, context: Dict[str, Any]) -> str:
        """
        Extract text content for AI generation.
        Context might specify chapter_id, file_path, timestamp, etc.
        """
        pass

    @abstractmethod
    def get_current_context(self) -> Dict[str, Any]:
        """
        What is the user currently viewing?
        Returns: { reference: "Chapter 5", page: 42, ... }
        """
        pass

    @abstractmethod
    def get_available_lab_types(self) -> List[str]:
        """What labs can be generated from this source?"""
        pass

    @abstractmethod
    def get_chat_context(self) -> Dict[str, Any]:
        """What context should chat have about this source?"""
        pass

    @abstractmethod
    def get_view_data(self) -> Dict[str, Any]:
        """
        Data the frontend needs to render this source.
        Frontend doesn't decide what to show — backend tells it.
        """
        pass

    # ─────────────────────────────────────────────
    # CACHING (handled by abstract class automatically)
    # ─────────────────────────────────────────────

    async def get_cache_id(self) -> Optional[str]:
        """
        Returns valid cache_id, creating/refreshing if needed.
        Called before any AI generation.
        """
        if self._is_cache_valid():
            return self.cache_id
        logger.warning("Cache invalid, creating new cache", source_id=str(self.id))
        return await self._create_cache()

    def _is_cache_valid(self) -> bool:
        """Check if current cache exists and hasn't expired"""
        if not self.cache_id or not self.cache_expires_at:
            return False
        return datetime.now(timezone.utc) < self.cache_expires_at
    
    @aiprovider_exception_wrapper
    async def _create_cache(self) -> Optional[str]:
        """Create new cache with AI provider"""
        logger.debug("Creating cache", source_id=str(self.id))

        content = await self.get_full_content()
        logger.debug("Retrieved content for caching", source_id=str(self.id), content_length=len(content))

        # Check if provider supports caching
        if not ai_provider.supports_caching():
          logger.info("AI provider doesn't support caching", source_id=str(self.id))
          return None

        if not self._source_service:
            logger.warning("No source service provided, cache won't be persisted", source_id=str(self.id))
            return None

        # Create cache with provider (e.g., Gemini)
        logger.info("Calling AI provider to create cache", source_id=str(self.id))
        cache_result = await ai_provider.create_cache(content)

        if cache_result:
            self.cache_id = cache_result.cache_id
            self.cache_expires_at = cache_result.expires_at
            logger.info("Cache created successfully",
                       source_id=str(self.id),
                       cache_id=self.cache_id,
                       expires_at=str(self.cache_expires_at))

            # Persist to database
            await self._source_service.update_source(self.id, SourceUpdate(cache_id=self.cache_id, cache_expires_at=self.cache_expires_at))
            logger.debug("Cache persisted to database", source_id=str(self.id))
        else:
            logger.warning("AI provider returned None for cache creation", source_id=str(self.id))

        return self.cache_id


    async def invalidate_cache(self) -> None:
        """Force cache refresh on next generation"""
        logger.info("Invalidating cache", source_id=str(self.id))

        self.cache_id = None
        self.cache_expires_at = None

        if self._source_service:
          await self._source_service.update_source(self.id, SourceUpdate(cache_id=None, cache_expires_at=None))
          logger.info("Cache invalidation persisted", source_id=str(self.id))
        else:
          logger.warning("No source service available, cache invalidation not persisted", source_id=str(self.id))


# Global registry mapping source type identifiers to Source classes
# Example: {"pdf": PDFSource, "github": GitHubSource}
source_registry: Dict[str, Type[Source]] = {}


def register_source(cls: Type[Source]) -> Type[Source]:
    """Decorator to register a source type in the global registry."""
    source_registry[cls.source_type] = cls
    logger.info("Registered source type", source_type=cls.source_type, source_class=cls.__name__)
    return cls
from app.config.exceptions import AIProviderException
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any, List, Optional, Type, TypeVar, cast
from abc import ABC, abstractmethod
from app.config.schemas import CacheResult
from app.config.logging import get_logger
from google import genai
from google.genai.client import Client as GeminiClient
from pydantic import BaseModel
from app.config.settings import settings

T = TypeVar("T", bound=BaseModel)

logger = get_logger(__name__)

DEFAULT_SYSTEM_INSTRUCTION = """You are an expert educational content analyzer for the AIDE learning platform.
Your role is to help users learn by creating interactive exercises, answering questions, and explaining concepts
based on the educational content (PDFs, documents, etc.) you have access to.

When generating content:
- Focus on practical, hands-on learning exercises
- Create clear, testable code challenges when appropriate
- Use the Socratic method to guide understanding rather than giving direct answers
- Reference specific sections of the source material when relevant
"""


@dataclass
class CacheConfig:
    """Configuration for creating an AI cache."""

    display_name: str
    system_instruction: str = DEFAULT_SYSTEM_INSTRUCTION
    ttl_seconds: Optional[int] = None  # If None, uses settings.ai_cache_ttl_seconds


class AIProvider[ClientT](ABC):
    """Abstract base class for AI providers, generic over the client type."""

    client: ClientT

    @abstractmethod
    def supports_caching(self) -> bool:
        pass

    @abstractmethod
    def create_cache(
        self, content: str | List[Any], config: Optional[CacheConfig] = None
    ) -> Optional[CacheResult]:
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        response_schema: Type[T],
        cache_id: Optional[str] = None,
    ) -> T:
        """Generate content using the AI provider.

        Args:
            prompt: The prompt to send to the AI
            response_schema: A Pydantic model class defining the expected response structure
            cache_id: Optional cache ID for cached content context

        Returns:
            An instance of the response_schema Pydantic model
        """
        pass


class GeminiProvider(AIProvider[GeminiClient]):
    def __init__(self):
        super().__init__()
        self.client: GeminiClient = genai.Client(api_key=settings.gemini_api_key)

    def supports_caching(self) -> bool:
        return True

    def create_cache(
        self, content: str | List[Any], config: Optional[CacheConfig] = None
    ) -> Optional[CacheResult]:
        cache_config = config or CacheConfig(display_name="aide-cache")
        ttl = cache_config.ttl_seconds or settings.ai_cache_ttl_seconds

        # Normalize content to list format for Gemini API
        content_list = [content] if isinstance(content, str) else content

        try:
            logger.info(
                "Creating Gemini cache",
                display_name=cache_config.display_name,
                ttl_seconds=ttl,
            )
            cache = self.client.caches.create(
                model=settings.gemini_model,
                config=genai.types.CreateCachedContentConfig(
                    display_name=cache_config.display_name,
                    system_instruction=cache_config.system_instruction,
                    contents=content_list,
                    ttl=f"{ttl}s",
                ),
            )
            if cache.name is None or cache.expire_time is None:
                logger.error("Cache created but missing name or expire_time")
                return None

            logger.info(
                "Cache created successfully",
                cache_id=cache.name,
                expires_at=str(cache.expire_time),
            )
            return CacheResult(
                cache_id=cache.name,
                expires_at=cache.expire_time,
            )
        except Exception as e:
            logger.error(f"Failed to create cache: {e}")
            return None

    def generate(
        self,
        prompt: str,
        response_schema: Type[T],
        cache_id: Optional[str] = None,
    ) -> T:
        """Generate structured content using Gemini with Pydantic schema validation.

        Args:
            prompt: The prompt to send to Gemini
            response_schema: A Pydantic model class for structured output
            cache_id: Optional cache ID for cached content context

        Returns:
            An instance of the response_schema Pydantic model
        """
        try:
            config = genai.types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema,
            )

            if cache_id:
                config.cached_content = cache_id

            logger.info(
                "Generating content with Gemini",
                schema=response_schema.__name__,
                has_cache=cache_id is not None,
            )

            response = self.client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
                config=config,
            )

            if response.text is None:
                raise AIProviderException("Gemini returned empty response")

            # Parse the JSON response into the Pydantic model
            return response_schema.model_validate_json(response.text)
        except AIProviderException:
            raise
        except Exception as e:
            logger.error("Failed to generate content", error=str(e))
            raise AIProviderException(f"Failed to generate content: {e}") from e


def aiprovider_exception_wrapper[Func: Callable[..., Any]](func: Func) -> Func:
    """Wrapper used to forward re-throw exceptions as AIProviderException."""

    @wraps(func)
    async def _decorated(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except Exception as exception:
            msg = f"AIProviderException error: {exception}"
            logger.exception(msg)
            raise AIProviderException(msg) from exception

    return cast("Func", _decorated)


ai_provider = GeminiProvider()

from app.config.exceptions import AIProviderException
from collections.abc import Callable
from functools import wraps
from typing import Any, cast

from app.config.logging import get_logger

logger = get_logger(__name__)

# todo
ai_provider = None


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

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from app.config.logging import get_logger

logger = get_logger(__name__)


class Lab(ABC):
    lab_type: str  # e.g., "code_lab"
    supported_sources: List[str] = []  # e.g., ["pdf", "github"]

    @classmethod
    @abstractmethod
    def get_action_metadata(cls) -> Dict[str, Any]:
        """Return the action metadata for this lab type."""
        pass

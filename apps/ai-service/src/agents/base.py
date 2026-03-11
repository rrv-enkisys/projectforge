from __future__ import annotations

"""Base class for all ProjectForge AI agents."""
import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base for all AI agents.

    Each concrete agent must declare a ``name`` and ``description`` class
    attribute and implement ``run()``.
    """

    name: str = "base_agent"
    description: str = ""

    @abstractmethod
    async def run(self, **kwargs: Any) -> Any:
        """Execute the agent's main task and return a structured result."""
        ...

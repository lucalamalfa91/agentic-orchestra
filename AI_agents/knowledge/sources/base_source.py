"""Base class for all knowledge sources."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Document:
    """A single document chunk retrieved from a knowledge source."""

    content: str
    source: str  # URL, file path, or API endpoint
    metadata: dict[str, Any] = field(default_factory=dict)


class KnowledgeSource(ABC):
    """
    Abstract base class for all knowledge sources.

    Each source must implement fetch() to retrieve documents
    and provide name/description properties.
    """

    @abstractmethod
    async def fetch(self, query: str) -> list[Document]:
        """
        Fetch documents relevant to the query from this source.

        Args:
            query: User query or requirements text to use for filtering/searching

        Returns:
            List of Document objects containing content chunks
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for this source instance."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this source provides."""
        pass

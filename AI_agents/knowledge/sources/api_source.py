"""API-based knowledge source - fetches content from REST APIs."""

import logging
from typing import Any, Optional

import httpx

from .base_source import KnowledgeSource, Document

logger = logging.getLogger(__name__)


class APISource(KnowledgeSource):
    """
    Fetches content from a REST API endpoint.

    Supports:
    - Custom authentication headers
    - JSON response parsing via dot-notation paths
    - Content chunking
    """

    def __init__(
        self,
        endpoint_url: str,
        auth_header: Optional[str] = None,
        auth_value: Optional[str] = None,
        response_path: str = "data",
        timeout: int = 30,
        chunk_size: int = 500,
    ):
        """
        Initialize the API source.

        Args:
            endpoint_url: Full URL of the API endpoint
            auth_header: Header name for authentication (e.g., "Authorization")
            auth_value: Header value (e.g., "Bearer <token>") - stored encrypted in DB
            response_path: Dot-notation path to content in JSON response (e.g., "data.items.content")
            timeout: Request timeout in seconds
            chunk_size: Approximate chunk size in words
        """
        self.endpoint_url = endpoint_url
        self.auth_header = auth_header
        self.auth_value = auth_value
        self.response_path = response_path
        self.timeout = timeout
        self.chunk_size = chunk_size

    @property
    def name(self) -> str:
        # Use endpoint path as identifier
        from urllib.parse import urlparse

        parsed = urlparse(self.endpoint_url)
        return f"api_{parsed.netloc}{parsed.path}".replace("/", "_")

    @property
    def description(self) -> str:
        return f"API endpoint: {self.endpoint_url}"

    async def fetch(self, query: str) -> list[Document]:
        """
        Fetch content from the API endpoint.

        Args:
            query: Not used for API calls (could be used for query params in future)

        Returns:
            List of Document chunks
        """
        logger.info(f"[APISource] Fetching from {self.endpoint_url}")

        headers = {}
        if self.auth_header and self.auth_value:
            headers[self.auth_header] = self.auth_value

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.endpoint_url, headers=headers)
                response.raise_for_status()

                json_data = response.json()

                # Extract content using dot-notation path
                content = self._extract_from_path(json_data, self.response_path)

                # Convert to string if needed
                if isinstance(content, list):
                    content = "\n\n".join(str(item) for item in content)
                elif not isinstance(content, str):
                    content = str(content)

                # Chunk content
                chunks = self._chunk_content(content)

                documents = [
                    Document(
                        content=chunk,
                        source=self.endpoint_url,
                        metadata={
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                            "response_path": self.response_path,
                        },
                    )
                    for i, chunk in enumerate(chunks)
                ]

                logger.info(f"[APISource] Extracted {len(documents)} chunks from API response")
                return documents

        except httpx.HTTPStatusError as e:
            logger.error(f"[APISource] HTTP error {e.response.status_code}: {e}")
            return []
        except Exception as e:
            logger.error(f"[APISource] Error fetching from API: {e}")
            return []

    def _extract_from_path(self, data: Any, path: str) -> Any:
        """
        Extract value from nested dict/list using dot notation.

        Example: "data.items.0.content" extracts data["items"][0]["content"]
        """
        parts = path.split(".")
        current = data

        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                try:
                    index = int(part)
                    current = current[index]
                except (ValueError, IndexError):
                    logger.warning(f"[APISource] Invalid path segment: {part}")
                    return None
            else:
                logger.warning(f"[APISource] Cannot traverse path at: {part}")
                return None

            if current is None:
                logger.warning(f"[APISource] Path not found: {path}")
                return None

        return current

    def _chunk_content(self, content: str) -> list[str]:
        """Split content into chunks."""
        if not content:
            return []

        words = content.split()
        chunks = []
        overlap = 50

        for i in range(0, len(words), self.chunk_size - overlap):
            chunk_words = words[i : i + self.chunk_size]
            chunk_text = " ".join(chunk_words)
            if chunk_text.strip():
                chunks.append(chunk_text)

        return chunks

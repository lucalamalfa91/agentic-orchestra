"""Web scraper knowledge source - crawls websites and extracts content."""

import asyncio
import logging
from typing import Optional
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

from .base_source import KnowledgeSource, Document

logger = logging.getLogger(__name__)


class WebScraperSource(KnowledgeSource):
    """
    Crawls a website and extracts content using CSS selectors.

    Supports:
    - Configurable base URL (any public or authenticated site)
    - CSS selectors for targeted content extraction
    - Depth-limited crawling
    - robots.txt compliance
    - Custom headers for authentication
    """

    def __init__(
        self,
        base_url: str,
        selectors: Optional[dict[str, str]] = None,
        max_pages: int = 20,
        crawl_depth: int = 2,
        headers: Optional[dict[str, str]] = None,
        timeout: int = 10,
    ):
        """
        Initialize the web scraper.

        Args:
            base_url: Starting URL to crawl from
            selectors: CSS selectors for content extraction (e.g., {"content": "article", "title": "h1"})
            max_pages: Maximum number of pages to crawl
            crawl_depth: Maximum link depth from base URL
            headers: Optional HTTP headers (for auth, user-agent, etc.)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.selectors = selectors or {"content": "body"}
        self.max_pages = max_pages
        self.crawl_depth = crawl_depth
        self.headers = headers or {}
        self.timeout = timeout

        # Set default user agent if not provided
        if "User-Agent" not in self.headers:
            self.headers["User-Agent"] = "AgenticOrchestra-KnowledgeAgent/1.0"

        self._visited_urls: set[str] = set()
        self._robot_parser: Optional[RobotFileParser] = None

    @property
    def name(self) -> str:
        domain = urlparse(self.base_url).netloc
        return f"web_{domain}"

    @property
    def description(self) -> str:
        return f"Web scraper for {self.base_url}"

    async def fetch(self, query: str) -> list[Document]:
        """
        Crawl the website and extract content.

        Args:
            query: Not used for web scraping (all pages crawled)

        Returns:
            List of Document chunks (~500 tokens each)
        """
        logger.info(f"[WebScraperSource] Starting crawl from {self.base_url}")

        # Check robots.txt
        await self._load_robots_txt()

        documents = []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Start crawling from base URL
            to_crawl = [(self.base_url, 0)]  # (url, depth)

            while to_crawl and len(self._visited_urls) < self.max_pages:
                url, depth = to_crawl.pop(0)

                if url in self._visited_urls or depth > self.crawl_depth:
                    continue

                if not self._can_fetch(url):
                    logger.debug(f"[WebScraperSource] Blocked by robots.txt: {url}")
                    continue

                try:
                    content, links = await self._fetch_page(client, url)
                    self._visited_urls.add(url)

                    # Chunk content into ~500 token segments
                    chunks = self._chunk_content(content)
                    for i, chunk in enumerate(chunks):
                        documents.append(
                            Document(
                                content=chunk,
                                source=url,
                                metadata={"chunk_index": i, "total_chunks": len(chunks)},
                            )
                        )

                    # Add child links to queue
                    if depth < self.crawl_depth:
                        for link in links:
                            to_crawl.append((link, depth + 1))

                except Exception as e:
                    logger.warning(f"[WebScraperSource] Failed to fetch {url}: {e}")

        logger.info(f"[WebScraperSource] Crawled {len(self._visited_urls)} pages, extracted {len(documents)} chunks")
        return documents

    async def _load_robots_txt(self):
        """Load and parse robots.txt for the domain."""
        try:
            parsed_url = urlparse(self.base_url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"

            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(robots_url, headers=self.headers)
                if response.status_code == 200:
                    self._robot_parser = RobotFileParser()
                    self._robot_parser.parse(response.text.splitlines())
                    logger.info(f"[WebScraperSource] Loaded robots.txt from {robots_url}")
        except Exception as e:
            logger.debug(f"[WebScraperSource] No robots.txt found or error: {e}")

    def _can_fetch(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt."""
        if not self._robot_parser:
            return True

        user_agent = self.headers.get("User-Agent", "*")
        return self._robot_parser.can_fetch(user_agent, url)

    async def _fetch_page(self, client: httpx.AsyncClient, url: str) -> tuple[str, list[str]]:
        """
        Fetch a single page and extract content + links.

        Returns:
            (extracted_text, child_links)
        """
        response = await client.get(url, headers=self.headers, follow_redirects=True)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract content using selectors
        extracted_text = []
        for selector_name, selector in self.selectors.items():
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(separator=" ", strip=True)
                if text:
                    extracted_text.append(text)

        # Find all internal links
        links = []
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            absolute_url = urljoin(url, href)

            # Only follow links within the same domain
            if urlparse(absolute_url).netloc == urlparse(self.base_url).netloc:
                links.append(absolute_url)

        content = "\n\n".join(extracted_text)
        return content, links

    def _chunk_content(self, content: str, chunk_size: int = 500) -> list[str]:
        """
        Split content into chunks of approximately chunk_size tokens.

        Uses simple word-based chunking with overlap.
        """
        if not content:
            return []

        words = content.split()
        chunks = []
        overlap = 50  # words

        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i : i + chunk_size]
            chunk_text = " ".join(chunk_words)
            if chunk_text.strip():
                chunks.append(chunk_text)

        return chunks

# Prompt 04 — Knowledge Agent (Generic RAG)

You are working on `lucalamalfa91/agentic-orchestra`.
Check `.claude/context/migration_status.md` before starting.
You have `AI_agents/graph/state.py` and `AI_agents/graph/graph.py`.

## Task: Create a generic, source-agnostic Knowledge Agent

The Knowledge Agent must work with ANY knowledge source, not just specific URLs.
The source is always configurable by the user via the UI.

## Files to create

### `AI_agents/knowledge/sources/base_source.py`
Abstract base class `KnowledgeSource`:
- `async def fetch(self, query: str) -> list[Document]`
- `@property name: str`
- `@property description: str`
`Document` dataclass: `content: str`, `source: str`, `metadata: dict`

### `AI_agents/knowledge/sources/web_scraper_source.py`
Implements `KnowledgeSource`. Constructor:
- `base_url: str` — any URL (internal wiki, public site, intranet, etc.)
- `selectors: dict` — optional CSS selectors for content extraction
- `max_pages: int = 20`
- `crawl_depth: int = 2`
Uses `httpx` + `BeautifulSoup`. Chunks content into ~500 token segments.
Respects `robots.txt`. Handles auth via optional `headers: dict` param.

### `AI_agents/knowledge/sources/file_source.py`
Implements `KnowledgeSource`. Constructor:
- `paths: list[str]` — local files or directories
Supports: `.pdf` (pypdf), `.md`, `.txt`, `.docx` (python-docx)
Chunks documents into ~500 token segments with overlap.

### `AI_agents/knowledge/sources/api_source.py`
Implements `KnowledgeSource`. Constructor:
- `endpoint_url: str`
- `auth_header: str` — header name (e.g. "Authorization")
- `auth_value: str` — header value (stored encrypted in DB, injected at runtime)
- `response_path: str` — dot-notation path to content in JSON response
Makes GET requests, extracts and chunks content.

### `AI_agents/knowledge/sources/__init__.py`
Exports all source classes.

### `AI_agents/knowledge/vector_store.py`
Class `VectorStoreService`:
- Uses `pgvector` via `asyncpg` — same `DATABASE_URL` as main app
- Embedding model: `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`
  (supports IT, EN, FR, DE)
- `async def upsert(source_name: str, documents: list[Document])`
  — deduplicates by content hash before inserting
- `async def search(query: str, top_k: int = 5) -> list[Document]`
  — cosine similarity search
- `async def create_table_if_not_exists()` — creates pgvector table on startup

### `AI_agents/knowledge/knowledge_agent.py`
Class `KnowledgeAgent`:
- Constructor: `sources: list[KnowledgeSource]`, `vector_store: VectorStoreService`
- `async def run(state: OrchestraState) -> OrchestraState`:
  1. Builds search query from `state["requirements"]`
  2. Searches `vector_store` for existing context
  3. If results < 3, triggers `fetch()` on all configured sources
  4. Upserts new documents to vector store
  5. Searches again, sets `state["rag_context"]` with top-5 results
  6. Updates agent status and returns state

### `AI_agents/knowledge/__init__.py`
Empty.

## Dependencies to add to `requirements.txt`
```
httpx
beautifulsoup4
pypdf
python-docx
sentence-transformers
pgvector
asyncpg
```

Write complete, working code for all files.
When done, update `.claude/context/migration_status.md` marking Prompt 04 complete
and list all files created.

"""Test that all Knowledge Agent modules can be imported (syntax check)."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("Knowledge Agent Import Test")
print("=" * 70)

# Test base classes
try:
    from AI_agents.knowledge.sources.base_source import KnowledgeSource, Document
    print("[OK] base_source: KnowledgeSource, Document")
except Exception as e:
    print(f"[FAIL] base_source: {e}")
    sys.exit(1)

# Test web scraper (will fail on httpx/bs4 imports, but syntax is valid)
try:
    import sys
    from io import StringIO
    from unittest.mock import MagicMock

    # Mock unavailable dependencies
    sys.modules['httpx'] = MagicMock()
    sys.modules['bs4'] = MagicMock()

    from AI_agents.knowledge.sources.web_scraper_source import WebScraperSource
    print("[OK] web_scraper_source: WebScraperSource")
except SyntaxError as e:
    print(f"[FAIL] web_scraper_source syntax: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[SKIP] web_scraper_source (missing deps): {type(e).__name__}")

# Test file source
try:
    from AI_agents.knowledge.sources.file_source import FileSource
    print("[OK] file_source: FileSource")
except SyntaxError as e:
    print(f"[FAIL] file_source syntax: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[SKIP] file_source (missing deps): {type(e).__name__}")

# Test API source
try:
    from AI_agents.knowledge.sources.api_source import APISource
    print("[OK] api_source: APISource")
except SyntaxError as e:
    print(f"[FAIL] api_source syntax: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[SKIP] api_source (missing deps): {type(e).__name__}")

# Test vector store
try:
    sys.modules['asyncpg'] = MagicMock()
    sys.modules['sentence_transformers'] = MagicMock()
    sys.modules['numpy'] = MagicMock()

    from AI_agents.knowledge.vector_store import VectorStoreService
    print("[OK] vector_store: VectorStoreService")
except SyntaxError as e:
    print(f"[FAIL] vector_store syntax: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[SKIP] vector_store (missing deps): {type(e).__name__}")

# Test knowledge agent
try:
    from AI_agents.knowledge.knowledge_agent import KnowledgeAgent
    print("[OK] knowledge_agent: KnowledgeAgent")
except SyntaxError as e:
    print(f"[FAIL] knowledge_agent syntax: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[SKIP] knowledge_agent (missing deps): {type(e).__name__}")

# Test package exports
try:
    from AI_agents.knowledge.sources import (
        KnowledgeSource,
        Document,
        WebScraperSource,
        FileSource,
        APISource,
    )
    print("[OK] sources package exports all classes")
except Exception as e:
    print(f"[FAIL] sources package: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("[OK] All Knowledge Agent modules have valid syntax!")
print("[INFO] Install dependencies from requirements-knowledge.txt to run")
print("=" * 70)

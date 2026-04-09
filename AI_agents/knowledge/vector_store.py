"""Vector store service using pgvector for semantic search."""

import hashlib
import logging
import os
from typing import Optional

import asyncpg
import numpy as np
from sentence_transformers import SentenceTransformer

from .sources.base_source import Document

logger = logging.getLogger(__name__)


class VectorStoreService:
    """
    Manages document embeddings and semantic search using pgvector.

    Features:
    - Multilingual embeddings (paraphrase-multilingual-mpnet-base-v2)
    - Content deduplication via SHA-256 hashing
    - Cosine similarity search
    - Automatic table creation
    """

    def __init__(
        self,
        database_url: Optional[str] = None,
        embedding_model: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        table_name: str = "knowledge_embeddings",
    ):
        """
        Initialize the vector store service.

        Args:
            database_url: PostgreSQL connection string (defaults to DATABASE_URL env var)
            embedding_model: HuggingFace model ID for embeddings
            table_name: Name of the pgvector table
        """
        self.database_url = database_url or os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")

        self.table_name = table_name
        self.embedding_model_name = embedding_model

        # Load embedding model (cached in memory)
        logger.info(f"[VectorStore] Loading embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        logger.info(f"[VectorStore] Embedding dimension: {self.embedding_dim}")

        self._pool: Optional[asyncpg.Pool] = None

    async def initialize(self):
        """Create connection pool and ensure table exists."""
        if not self._pool:
            self._pool = await asyncpg.create_pool(self.database_url, min_size=2, max_size=10)
            logger.info("[VectorStore] Connection pool created")

        await self.create_table_if_not_exists()

    async def close(self):
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            logger.info("[VectorStore] Connection pool closed")

    async def create_table_if_not_exists(self):
        """Create the pgvector table if it doesn't exist."""
        if not self._pool:
            raise RuntimeError("VectorStoreService not initialized - call initialize() first")

        async with self._pool.acquire() as conn:
            # Enable pgvector extension
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")

            # Create table with vector column
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                source TEXT NOT NULL,
                metadata JSONB DEFAULT '{{}}',
                content_hash TEXT UNIQUE NOT NULL,
                embedding vector({self.embedding_dim}) NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
            """
            await conn.execute(create_table_sql)

            # Create index for fast similarity search
            index_sql = f"""
            CREATE INDEX IF NOT EXISTS {self.table_name}_embedding_idx
            ON {self.table_name} USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100)
            """
            await conn.execute(index_sql)

            logger.info(f"[VectorStore] Table '{self.table_name}' ready")

    async def upsert(self, source_name: str, documents: list[Document]):
        """
        Insert or update documents in the vector store.

        Deduplicates by content hash before inserting.

        Args:
            source_name: Name of the knowledge source
            documents: List of Document objects to store
        """
        if not self._pool:
            raise RuntimeError("VectorStoreService not initialized")

        if not documents:
            logger.info("[VectorStore] No documents to upsert")
            return

        logger.info(f"[VectorStore] Upserting {len(documents)} documents from source '{source_name}'")

        # Generate embeddings for all documents
        contents = [doc.content for doc in documents]
        embeddings = self.embedding_model.encode(contents, show_progress_bar=False)

        # Prepare data with content hashes
        records = []
        for doc, embedding in zip(documents, embeddings):
            content_hash = self._hash_content(doc.content)
            records.append(
                {
                    "content": doc.content,
                    "source": doc.source,
                    "metadata": doc.metadata,
                    "content_hash": content_hash,
                    "embedding": embedding.tolist(),
                }
            )

        # Batch insert with conflict resolution (skip duplicates)
        async with self._pool.acquire() as conn:
            inserted_count = 0
            for record in records:
                try:
                    insert_sql = f"""
                    INSERT INTO {self.table_name} (content, source, metadata, content_hash, embedding)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (content_hash) DO NOTHING
                    """
                    result = await conn.execute(
                        insert_sql,
                        record["content"],
                        record["source"],
                        record["metadata"],
                        record["content_hash"],
                        record["embedding"],
                    )
                    # Check if row was inserted (not a duplicate)
                    if "INSERT" in result:
                        inserted_count += 1

                except Exception as e:
                    logger.error(f"[VectorStore] Error inserting document: {e}")

        logger.info(f"[VectorStore] Inserted {inserted_count} new documents (skipped {len(records) - inserted_count} duplicates)")

    async def search(self, query: str, top_k: int = 5) -> list[Document]:
        """
        Semantic search for documents similar to the query.

        Args:
            query: Search query text
            top_k: Number of top results to return

        Returns:
            List of Document objects ranked by similarity
        """
        if not self._pool:
            raise RuntimeError("VectorStoreService not initialized")

        # Generate query embedding
        query_embedding = self.embedding_model.encode(query, show_progress_bar=False)

        # Search using cosine similarity
        async with self._pool.acquire() as conn:
            search_sql = f"""
            SELECT content, source, metadata, (1 - (embedding <=> $1)) AS similarity
            FROM {self.table_name}
            ORDER BY embedding <=> $1
            LIMIT $2
            """
            rows = await conn.fetch(search_sql, query_embedding.tolist(), top_k)

        # Convert to Document objects
        documents = [
            Document(
                content=row["content"],
                source=row["source"],
                metadata=dict(row["metadata"]) if row["metadata"] else {},
            )
            for row in rows
        ]

        logger.info(f"[VectorStore] Found {len(documents)} results for query")
        return documents

    def _hash_content(self, content: str) -> str:
        """Generate SHA-256 hash of content for deduplication."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

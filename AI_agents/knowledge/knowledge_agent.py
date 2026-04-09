"""Knowledge Agent - orchestrates RAG retrieval for MVP generation."""

import logging
from typing import Optional

from ..graph.state import OrchestraState, AgentStatus
from .sources.base_source import KnowledgeSource
from .vector_store import VectorStoreService

logger = logging.getLogger(__name__)


class KnowledgeAgent:
    """
    Knowledge Agent retrieves relevant context from configured sources.

    Flow:
    1. Search existing vector store for relevant docs
    2. If insufficient results, fetch fresh content from sources
    3. Upsert new content to vector store
    4. Return top-K results in state["rag_context"]
    """

    def __init__(
        self,
        sources: list[KnowledgeSource],
        vector_store: VectorStoreService,
        min_results_threshold: int = 3,
        top_k: int = 5,
    ):
        """
        Initialize the Knowledge Agent.

        Args:
            sources: List of configured knowledge sources
            vector_store: Vector store service instance
            min_results_threshold: Minimum results before triggering fresh fetch
            top_k: Number of top results to return in RAG context
        """
        self.sources = sources
        self.vector_store = vector_store
        self.min_results_threshold = min_results_threshold
        self.top_k = top_k

    async def run(self, state: OrchestraState) -> OrchestraState:
        """
        Execute knowledge retrieval and update state.

        Args:
            state: Current orchestration state

        Returns:
            Updated state with rag_context populated
        """
        logger.info("[KnowledgeAgent] Starting knowledge retrieval")

        try:
            # Update status
            state["current_step"] = "knowledge_retrieval"
            state["agent_statuses"]["knowledge_retrieval"] = AgentStatus.RUNNING

            # Build search query from requirements
            query = self._build_search_query(state)
            logger.info(f"[KnowledgeAgent] Search query: {query[:100]}...")

            # Search existing vector store
            existing_docs = await self.vector_store.search(query, top_k=self.top_k)
            logger.info(f"[KnowledgeAgent] Found {len(existing_docs)} existing docs")

            # If insufficient results, fetch fresh content
            if len(existing_docs) < self.min_results_threshold:
                logger.info("[KnowledgeAgent] Insufficient results - fetching fresh content from sources")
                await self._fetch_and_index_sources(query)

                # Search again after indexing
                existing_docs = await self.vector_store.search(query, top_k=self.top_k)
                logger.info(f"[KnowledgeAgent] Found {len(existing_docs)} docs after fresh fetch")

            # Format results for RAG context
            rag_context = self._format_rag_context(existing_docs)
            state["rag_context"] = rag_context

            # Mark as completed
            state["completed_steps"].append("knowledge_retrieval")
            state["agent_statuses"]["knowledge_retrieval"] = AgentStatus.COMPLETED

            logger.info(f"[KnowledgeAgent] Completed - {len(existing_docs)} documents in RAG context")
            return state

        except Exception as e:
            logger.error(f"[KnowledgeAgent] Error during retrieval: {e}", exc_info=True)

            # Mark as failed and store error
            state["errors"]["knowledge_retrieval"] = str(e)
            state["agent_statuses"]["knowledge_retrieval"] = AgentStatus.FAILED
            state["current_step"] = "knowledge_retrieval_failed"

            return state

    def _build_search_query(self, state: OrchestraState) -> str:
        """
        Build search query from user requirements.

        Combines requirements text with optional tech stack hints.
        """
        query_parts = []

        if state["requirements"]:
            query_parts.append(state["requirements"])

        if state["tech_stack"]:
            tech_hints = ", ".join(state["tech_stack"])
            query_parts.append(f"Technology: {tech_hints}")

        return " ".join(query_parts)

    async def _fetch_and_index_sources(self, query: str):
        """
        Fetch fresh content from all configured sources and index it.

        Args:
            query: Search query to pass to sources (some sources may ignore it)
        """
        for source in self.sources:
            try:
                logger.info(f"[KnowledgeAgent] Fetching from source: {source.name}")

                # Fetch documents from source
                documents = await source.fetch(query)

                if documents:
                    # Upsert to vector store (deduplicates automatically)
                    await self.vector_store.upsert(source.name, documents)
                    logger.info(f"[KnowledgeAgent] Indexed {len(documents)} docs from {source.name}")
                else:
                    logger.warning(f"[KnowledgeAgent] No documents returned from {source.name}")

            except Exception as e:
                logger.error(f"[KnowledgeAgent] Error fetching from {source.name}: {e}")
                # Continue with other sources

    def _format_rag_context(self, documents: list) -> str:
        """
        Format retrieved documents into a single context string.

        Returns:
            Formatted string with document contents separated by markers
        """
        if not documents:
            return ""

        context_parts = []
        for i, doc in enumerate(documents, 1):
            context_parts.append(f"[Document {i} - Source: {doc.source}]")
            context_parts.append(doc.content)
            context_parts.append("")  # Empty line separator

        return "\n".join(context_parts)

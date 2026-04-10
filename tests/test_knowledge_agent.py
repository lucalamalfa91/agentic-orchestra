"""Tests for Knowledge Agent RAG functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from AI_agents.knowledge.knowledge_agent import KnowledgeAgent
from AI_agents.knowledge.sources.base_source import Document
from AI_agents.graph.state import AgentStatus


@pytest.fixture
def knowledge_agent(mock_vector_store, mock_knowledge_source):
    """KnowledgeAgent instance with mocked dependencies."""
    return KnowledgeAgent(
        sources=[mock_knowledge_source],
        vector_store=mock_vector_store,
        min_results_threshold=3,
        top_k=5,
    )


@pytest.mark.asyncio
@pytest.mark.unit
async def test_empty_store_triggers_fetch(knowledge_agent, mock_state, mock_vector_store, mock_knowledge_source, mock_documents):
    """Test that empty search results trigger fresh fetch from sources."""
    # Configure mock to return empty results first, then populated results after fetch
    mock_vector_store.search.side_effect = [
        [],  # First call: empty (triggers fetch)
        mock_documents[:5],  # Second call: populated after fetch
    ]
    mock_knowledge_source.fetch.return_value = mock_documents

    # Run agent
    result_state = await knowledge_agent.run(mock_state)

    # Verify fetch was called (because initial search returned empty)
    mock_knowledge_source.fetch.assert_called_once()

    # Verify upsert was called with fetched documents
    mock_vector_store.upsert.assert_called_once()
    call_args = mock_vector_store.upsert.call_args
    assert len(call_args[0][1]) == 3  # 3 documents from mock_documents

    # Verify search was called twice (before and after fetch)
    assert mock_vector_store.search.call_count == 2

    # Verify state updates
    assert result_state["agent_statuses"]["knowledge_retrieval"] == AgentStatus.COMPLETED
    assert "knowledge_retrieval" in result_state["completed_steps"]
    assert isinstance(result_state["rag_context"], str)
    assert len(result_state["rag_context"]) > 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_populated_store_skips_fetch(knowledge_agent, mock_state, mock_vector_store, mock_knowledge_source, mock_documents):
    """Test that sufficient search results skip fresh fetch."""
    # Configure mock to return enough results (>= min_results_threshold)
    mock_vector_store.search.return_value = mock_documents[:5]

    # Run agent
    result_state = await knowledge_agent.run(mock_state)

    # Verify fetch was NOT called (sufficient results already exist)
    mock_knowledge_source.fetch.assert_not_called()

    # Verify upsert was NOT called
    mock_vector_store.upsert.assert_not_called()

    # Verify search was called only once (no second search needed)
    assert mock_vector_store.search.call_count == 1

    # Verify state updates
    assert result_state["agent_statuses"]["knowledge_retrieval"] == AgentStatus.COMPLETED
    assert "knowledge_retrieval" in result_state["completed_steps"]
    assert isinstance(result_state["rag_context"], str)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_multilingual_query(knowledge_agent, mock_state, mock_vector_store, mock_documents):
    """Test that agent handles Italian and English queries without error."""
    mock_vector_store.search.return_value = mock_documents[:3]

    # Italian query
    mock_state["requirements"] = "Crea un'applicazione web per la gestione di task"
    result_it = await knowledge_agent.run(mock_state)
    assert result_it["agent_statuses"]["knowledge_retrieval"] == AgentStatus.COMPLETED
    assert "errors" not in result_it or "knowledge_retrieval" not in result_it["errors"]

    # Reset state
    mock_state["agent_statuses"]["knowledge_retrieval"] = AgentStatus.PENDING
    mock_state["completed_steps"] = []
    mock_state["rag_context"] = []

    # English query
    mock_state["requirements"] = "Build a task management web application"
    result_en = await knowledge_agent.run(mock_state)
    assert result_en["agent_statuses"]["knowledge_retrieval"] == AgentStatus.COMPLETED
    assert "errors" not in result_en or "knowledge_retrieval" not in result_en["errors"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_source_fetch_failure_is_graceful(knowledge_agent, mock_state, mock_vector_store, mock_knowledge_source):
    """Test that source fetch failures don't crash the agent."""
    # Configure source to raise exception
    mock_knowledge_source.fetch.side_effect = Exception("Network timeout")

    # Configure vector store to return empty (triggers fetch)
    mock_vector_store.search.side_effect = [
        [],  # First call: empty (triggers fetch)
        [],  # Second call: still empty after failed fetch
    ]

    # Run agent - should complete despite source failure
    with patch("AI_agents.knowledge.knowledge_agent.logger") as mock_logger:
        result_state = await knowledge_agent.run(mock_state)

    # Verify error was logged but agent completed
    mock_logger.error.assert_called()

    # Agent should complete successfully even if sources fail
    assert result_state["agent_statuses"]["knowledge_retrieval"] == AgentStatus.COMPLETED

    # RAG context should be empty but state should not have error
    # (source failures are logged but don't fail the agent)
    assert isinstance(result_state["rag_context"], str)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_rag_context_set_in_state(knowledge_agent, mock_state, mock_vector_store, mock_documents):
    """Test that rag_context is populated with Document objects after run."""
    # Configure mock to return documents
    mock_vector_store.search.return_value = mock_documents[:3]

    # Run agent
    result_state = await knowledge_agent.run(mock_state)

    # Verify rag_context is populated
    assert "rag_context" in result_state
    assert isinstance(result_state["rag_context"], str)
    assert len(result_state["rag_context"]) > 0

    # Verify formatted context contains document markers
    assert "[Document 1" in result_state["rag_context"]
    assert "Source:" in result_state["rag_context"]

    # Verify all documents are included
    for doc in mock_documents[:3]:
        assert doc.content in result_state["rag_context"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_vector_store_exception_fails_agent(knowledge_agent, mock_state, mock_vector_store):
    """Test that vector store exceptions set agent to FAILED status."""
    # Configure vector store to raise exception
    mock_vector_store.search.side_effect = Exception("Database connection failed")

    # Run agent
    result_state = await knowledge_agent.run(mock_state)

    # Verify agent failed
    assert result_state["agent_statuses"]["knowledge_retrieval"] == AgentStatus.FAILED

    # Verify error is recorded
    assert "knowledge_retrieval" in result_state["errors"]
    assert "Database connection failed" in result_state["errors"]["knowledge_retrieval"]

    # Verify current_step indicates failure
    assert "failed" in result_state["current_step"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_min_results_threshold_behavior():
    """Test that min_results_threshold controls fetch triggering."""
    mock_store = MagicMock()
    mock_store.search = AsyncMock(return_value=[
        Document(content="Doc 1", metadata={}, source_id="s1"),
        Document(content="Doc 2", metadata={}, source_id="s2"),
    ])
    mock_store.upsert = AsyncMock()

    mock_source = MagicMock()
    mock_source.fetch = AsyncMock(return_value=[])

    # Agent with threshold=3 (should trigger fetch with 2 results)
    agent_high = KnowledgeAgent(
        sources=[mock_source],
        vector_store=mock_store,
        min_results_threshold=3,
        top_k=5,
    )

    state = {
        "requirements": "Test",
        "user_id": "u1",
        "project_id": "p1",
        "features": [],
        "rag_context": [],
        "design_yaml": {},
        "api_schema": {},
        "db_schema": {},
        "backend_code": {},
        "frontend_code": {},
        "backlog_items": [],
        "devops_config": {},
        "github_repo_url": "",
        "current_step": "START",
        "completed_steps": [],
        "agent_statuses": {
            "knowledge_retrieval": AgentStatus.PENDING,
            "design": AgentStatus.PENDING,
            "backend_agent": AgentStatus.PENDING,
            "frontend_agent": AgentStatus.PENDING,
            "backlog_agent": AgentStatus.PENDING,
            "integration_check": AgentStatus.PENDING,
            "error_handler": AgentStatus.PENDING,
            "devops_agent": AgentStatus.PENDING,
            "publish_agent": AgentStatus.PENDING,
        },
        "errors": {},
    }

    await agent_high.run(state)

    # With 2 results and threshold=3, fetch should be called
    mock_source.fetch.assert_called_once()

    # Reset mocks
    mock_source.fetch.reset_mock()
    state["agent_statuses"]["knowledge_retrieval"] = AgentStatus.PENDING
    state["completed_steps"] = []

    # Agent with threshold=2 (should NOT trigger fetch with 2 results)
    agent_low = KnowledgeAgent(
        sources=[mock_source],
        vector_store=mock_store,
        min_results_threshold=2,
        top_k=5,
    )

    await agent_low.run(state)

    # With 2 results and threshold=2, fetch should NOT be called
    mock_source.fetch.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_top_k_parameter(mock_vector_store):
    """Test that top_k parameter controls number of returned documents."""
    # Create 10 mock documents
    many_docs = [
        Document(content=f"Doc {i}", metadata={}, source_id=f"s{i}")
        for i in range(10)
    ]

    mock_vector_store.search.return_value = many_docs
    mock_source = MagicMock()
    mock_source.fetch = AsyncMock(return_value=[])

    # Agent with top_k=3
    agent = KnowledgeAgent(
        sources=[mock_source],
        vector_store=mock_vector_store,
        min_results_threshold=1,
        top_k=3,
    )

    state = {
        "requirements": "Test",
        "user_id": "u1",
        "project_id": "p1",
        "features": [],
        "rag_context": [],
        "design_yaml": {},
        "api_schema": {},
        "db_schema": {},
        "backend_code": {},
        "frontend_code": {},
        "backlog_items": [],
        "devops_config": {},
        "github_repo_url": "",
        "current_step": "START",
        "completed_steps": [],
        "agent_statuses": {
            "knowledge_retrieval": AgentStatus.PENDING,
            "design": AgentStatus.PENDING,
            "backend_agent": AgentStatus.PENDING,
            "frontend_agent": AgentStatus.PENDING,
            "backlog_agent": AgentStatus.PENDING,
            "integration_check": AgentStatus.PENDING,
            "error_handler": AgentStatus.PENDING,
            "devops_agent": AgentStatus.PENDING,
            "publish_agent": AgentStatus.PENDING,
        },
        "errors": {},
    }

    await agent.run(state)

    # Verify search was called with top_k=3
    mock_vector_store.search.assert_called()
    call_kwargs = mock_vector_store.search.call_args[1]
    assert call_kwargs["top_k"] == 3

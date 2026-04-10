# Test Suite — Agentic Orchestra

Comprehensive test coverage for all AI components, LangGraph orchestration, and MCP servers.

## Test Structure

```
tests/
├── conftest.py                  # Shared fixtures (mock_state, mock_llm, etc.)
├── test_graph_state.py          # OrchestraState and AgentStatus tests
├── test_knowledge_agent.py      # RAG and Knowledge Agent tests
├── test_graph_flow.py           # LangGraph integration tests
└── test_mcp_servers.py          # MCP server tests
```

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables** (for some tests):
   ```bash
   export DATABASE_URL="postgresql://user:pass@localhost/testdb"
   export OPENAI_API_KEY="sk-..."
   export ANTHROPIC_API_KEY="sk-ant-..."
   ```

   Note: Most tests use mocks and don't require real API keys.

## Running Tests

### Run all tests
```bash
pytest tests/
```

### Run specific test file
```bash
pytest tests/test_graph_state.py
```

### Run with coverage
```bash
pytest tests/ --cov=AI_agents --cov-report=html
```

### Run only unit tests (fast)
```bash
pytest tests/ -m unit
```

### Run only integration tests
```bash
pytest tests/ -m integration
```

### Run with verbose output
```bash
pytest tests/ -v
```

## Test Categories

### Unit Tests (`-m unit`)
- **test_graph_state.py**: OrchestraState instantiation, AgentStatus transitions, state updates
- **test_knowledge_agent.py**: Knowledge retrieval, vector store operations, RAG context
- **test_mcp_servers.py**: MCP tool schemas, auth errors, logging, response formatting

### Integration Tests (`-m integration`)
- **test_graph_flow.py**: End-to-end LangGraph execution, parallel nodes, error routing

## Fixtures (conftest.py)

### State Fixtures
- `mock_state`: Minimal valid OrchestraState with all required fields
- `sample_design_yaml`: Sample design output
- `sample_api_schema`: Sample API endpoint schema
- `sample_db_schema`: Sample database schema

### Agent Fixtures
- `mock_llm`: Mocked LangChain LLM (returns fixed DesignSchema)
- `mock_vector_store`: Mocked VectorStoreService
- `mock_mcp_client`: Mocked MCPClientManager
- `mock_knowledge_source`: Mocked KnowledgeSource
- `mock_documents`: Sample Document objects

## Test Coverage

### State Management (7 tests)
- ✓ OrchestraState instantiation with required fields
- ✓ AgentStatus enum values and transitions
- ✓ Errors dict updates per agent
- ✓ Completed steps append and order preservation
- ✓ Agent statuses update
- ✓ Current step update
- ✓ State with all fields populated

### Knowledge Agent (9 tests)
- ✓ Empty store triggers fresh fetch from sources
- ✓ Populated store skips fetch
- ✓ Multilingual query handling (Italian/English)
- ✓ Source fetch failure is graceful
- ✓ RAG context set in state
- ✓ Vector store exception fails agent
- ✓ Min results threshold behavior
- ✓ Top-K parameter controls results
- ✓ Document formatting

### Graph Flow (6 tests)
- ✓ Graph runs end-to-end from START to END
- ✓ Backend agent failure routes to error_handler
- ✓ Parallel nodes all update state
- ✓ State preserved across nodes
- ✓ Route after integration check (no errors → devops)
- ✓ Route after integration check (errors → error_handler)

### MCP Servers (17 tests)
- ✓ GitHub server tool list
- ✓ GitHub server has required tools
- ✓ Push files tool schema validation
- ✓ Missing token raises MCPAuthError
- ✓ Inject token returns value
- ✓ Empty token raises MCPAuthError
- ✓ Tool calls logged with decorator
- ✓ Tool call logs duration
- ✓ Tool call logs errors
- ✓ Tool call logs auth errors separately
- ✓ Format error response for MCPAuthError
- ✓ Format error response for generic error
- ✓ Format success response
- ✓ Success response with various data types
- ✓ MCPAuthError is Exception subclass
- ✓ Azure DevOps server tool list
- ✓ Deploy server tool list

## Troubleshooting

### Import errors
If you see `ModuleNotFoundError`, ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Database connection errors (integration tests)
Integration tests that use the database checkpointer require a valid `DATABASE_URL`:
```bash
export DATABASE_URL="postgresql://localhost/orchestrator_test"
```

Or run only unit tests to skip database-dependent tests:
```bash
pytest tests/ -m unit
```

### Missing model downloads (knowledge_agent tests)
The `sentence-transformers` model is downloaded on first run. If tests fail due to download issues, ensure you have internet connectivity and sufficient disk space (~500MB).

## Adding New Tests

1. **Create test file** in `tests/` with `test_` prefix
2. **Import fixtures** from `conftest.py`
3. **Mark tests** with `@pytest.mark.unit` or `@pytest.mark.integration`
4. **Use async fixtures** for async tests with `@pytest.mark.asyncio`
5. **Follow naming convention**: `test_{what}_{condition}_{expected}`

Example:
```python
@pytest.mark.asyncio
@pytest.mark.unit
async def test_agent_failure_sets_error_state(mock_state, mock_llm):
    # Test implementation
    pass
```

## CI/CD Integration

The test suite is designed to run in CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest tests/ -v --junitxml=test-results.xml
```

## Related Documentation

- **LangGraph Graph**: `AI_agents/graph/graph.py`
- **OrchestraState**: `AI_agents/graph/state.py`
- **Knowledge Agent**: `AI_agents/knowledge/knowledge_agent.py`
- **MCP Servers**: `mcp_servers/README.md`

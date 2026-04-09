# Prompt 07b — BaseAgent Abstraction

You are working on `lucalamalfa91/agentic-orchestra`.
Check `.claude/context/migration_status.md` before starting.
All real agent nodes have been implemented in `AI_agents/graph/nodes/`.
The `get_llm_client()` factory is already available in `AI_agents/utils/llm_client.py`.

## Context

The current agent nodes share a repeated pattern:
- build a prompt string manually
- call the LLM directly
- parse and validate output
- update `OrchestraState` fields
- handle exceptions and set `state["errors"]`

This prompt introduces a shared `BaseAgent` abstraction to eliminate that
duplication, making every agent consistent and easy to extend.

## Task: Create `AI_agents/base_agent.py`

Define an abstract class `BaseAgent` that every agent node can extend.

### Requirements

```python
from abc import ABC, abstractmethod
from typing import Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from AI_agents.utils.llm_client import get_llm_client
from AI_agents.graph.state import OrchestraState, AgentStatus
import logging, time

class BaseAgent(ABC):
    """
    Shared foundation for all agent nodes.
    Centralizes: LLM init, prompt rendering, retries, logging, error handling.
    Subclasses implement only `build_prompt()` and `parse_output()`.
    """

    MAX_RETRIES: int = 2
    agent_name: str = "base"  # override in subclass

    def __init__(self):
        # LLM is lazy-initialized at invoke time so provider/key come from state
        self._chain = None

    def _build_chain(self, provider: str, config: dict):
        llm = get_llm_client(provider, config)
        return ChatPromptTemplate.from_messages([
            ("system", self.system_prompt()),
            ("human", "{input}")
        ]) | llm | StrOutputParser()

    @abstractmethod
    def system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        pass

    @abstractmethod
    def build_input(self, state: OrchestraState) -> str:
        """Build the human message content from state."""
        pass

    @abstractmethod
    def parse_output(self, raw: str, state: OrchestraState) -> OrchestraState:
        """Parse LLM response and write results into state. Return updated state."""
        pass

    async def run(self, state: OrchestraState) -> OrchestraState:
        logger = logging.getLogger(self.agent_name)
        logger.info(f"[{self.agent_name}] starting")

        state["current_step"] = self.agent_name
        state["agent_statuses"][self.agent_name] = AgentStatus.RUNNING

        provider = state.get("ai_provider", "anthropic")
        config = {}  # extend if needed for model/temperature overrides

        chain = self._build_chain(provider, config)
        user_input = self.build_input(state)

        for attempt in range(1, self.MAX_RETRIES + 2):
            try:
                start = time.monotonic()
                raw = await chain.ainvoke({"input": user_input})
                elapsed = time.monotonic() - start
                logger.info(f"[{self.agent_name}] LLM call ok ({elapsed:.1f}s)")
                state = self.parse_output(raw, state)
                state["completed_steps"].append(self.agent_name)
                state["agent_statuses"][self.agent_name] = AgentStatus.COMPLETED
                return state
            except Exception as e:
                logger.warning(f"[{self.agent_name}] attempt {attempt} failed: {e}")
                if attempt > self.MAX_RETRIES:
                    state["errors"][self.agent_name] = str(e)
                    state["agent_statuses"][self.agent_name] = AgentStatus.FAILED
                    return state

        return state  # unreachable but satisfies type checker
```

### Rules
- Do NOT change any existing agent node files yet — this is additive only.
- Do NOT change `graph.py`, `state.py`, or `llm_client.py`.
- Add `anthropic` and `langchain-anthropic` to `requirements.txt` if not present.
- Write a short docstring at the top of the file explaining the design pattern.

## Task: Create `AI_agents/base_agent_test_demo.py`

A minimal standalone demo (NOT a pytest test) that instantiates a concrete
`BaseAgent` subclass inline and calls `run()` with a minimal fake `OrchestraState`.
This verifies the abstraction works without running the full graph.

```python
# Demo only — delete after validating BaseAgent works
class EchoAgent(BaseAgent):
    agent_name = "echo"
    def system_prompt(self): return "You repeat back the user's message."
    def build_input(self, state): return state["requirements"]
    def parse_output(self, raw, state):
        state["design_yaml"] = {"echo": raw[:100]}
        return state

import asyncio
asyncio.run(EchoAgent().run({
    "requirements": "Hello world",
    "ai_provider": "anthropic",
    "errors": {},
    "completed_steps": [],
    "agent_statuses": {},
    "current_step": "",
}))
```

When done, update `.claude/context/migration_status.md` marking Prompt 07b complete.

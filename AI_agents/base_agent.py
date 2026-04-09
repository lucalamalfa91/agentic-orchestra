"""
BaseAgent Abstraction — Shared foundation for all Orchestra agent nodes.

Design Pattern:
    Every agent node in this project shares common responsibilities:
    - Initialize LLM client based on provider/config
    - Render prompt templates with state data
    - Execute LLM calls with retry logic
    - Parse and validate LLM output
    - Update OrchestraState fields consistently
    - Handle exceptions gracefully without crashing the graph

This abstraction centralizes all that boilerplate. Concrete agents only implement:
    1. system_prompt() — defines agent's role and output format
    2. build_input() — constructs user message from OrchestraState
    3. parse_output() — writes LLM response into OrchestraState

Benefits:
    - Consistency: All agents follow the same error handling and logging pattern
    - DRY: No duplicated retry/logging/state-update code
    - Maintainability: Change retry logic once, affects all agents
    - Testability: Easy to mock BaseAgent.run() for unit tests

Usage:
    class MyAgent(BaseAgent):
        agent_name = "my_agent"

        def system_prompt(self) -> str:
            return "You are an expert at..."

        def build_input(self, state: OrchestraState) -> str:
            return f"Requirements: {state['requirements']}"

        def parse_output(self, raw: str, state: OrchestraState) -> OrchestraState:
            state["my_output"] = process(raw)
            return state

    # In graph node:
    async def my_agent_node(state: OrchestraState) -> OrchestraState:
        return await MyAgent().run(state)

Created: Prompt 07b (2026-04-09)
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from AI_agents.utils.llm_client import get_llm_client
from AI_agents.graph.state import OrchestraState, AgentStatus
import logging
import time


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
        """
        Construct the LangChain LCEL chain: prompt | llm | parser.

        Args:
            provider: "openai" or "anthropic"
            config: dict with optional model, temperature, max_tokens overrides

        Returns:
            Runnable chain ready for .ainvoke()
        """
        llm = get_llm_client(provider, config)
        return ChatPromptTemplate.from_messages([
            ("system", self.system_prompt()),
            ("human", "{input}")
        ]) | llm | StrOutputParser()

    @abstractmethod
    def system_prompt(self) -> str:
        """
        Return the system prompt for this agent.

        This defines the agent's role, expertise, and output format.
        Example: "You are an expert backend architect. Generate..."
        """
        pass

    @abstractmethod
    def build_input(self, state: OrchestraState) -> str:
        """
        Build the human message content from state.

        Extract relevant fields from OrchestraState and format them
        into a clear user prompt for the LLM.

        Args:
            state: Current OrchestraState with all agent data

        Returns:
            String formatted for human message slot
        """
        pass

    @abstractmethod
    def parse_output(self, raw: str, state: OrchestraState) -> OrchestraState:
        """
        Parse LLM response and write results into state.

        Validate and transform the LLM's string output, then populate
        the appropriate OrchestraState fields (e.g., design_yaml, backend_code).

        Args:
            raw: Raw string output from LLM
            state: OrchestraState to update

        Returns:
            Updated state (must return, not mutate in place for type safety)

        Raises:
            May raise exceptions on parse failure — BaseAgent.run() will catch them
        """
        pass

    async def run(self, state: OrchestraState) -> OrchestraState:
        """
        Execute the agent with retry logic and error handling.

        Workflow:
            1. Update state to mark agent as RUNNING
            2. Initialize LLM chain with provider from state
            3. Build input prompt from state data
            4. Attempt LLM call (up to MAX_RETRIES + 1 total attempts)
            5. Parse output and update state on success
            6. Mark agent as COMPLETED or FAILED

        Error handling:
            - Logs all attempts and failures
            - On final failure, sets state["errors"][agent_name] = error_msg
            - Never raises exceptions (returns state with FAILED status instead)

        Args:
            state: Current OrchestraState from graph

        Returns:
            Updated OrchestraState (COMPLETED or FAILED)
        """
        logger = logging.getLogger(self.agent_name)
        logger.info(f"[{self.agent_name}] starting")

        # Mark agent as running
        state["current_step"] = self.agent_name
        state["agent_statuses"][self.agent_name] = AgentStatus.RUNNING

        # Get AI provider config from state (injected by orchestrator)
        provider = state.get("ai_provider", "anthropic")
        config: Dict[str, Any] = {}  # Extend if needed for model/temperature overrides

        # Build LCEL chain
        chain = self._build_chain(provider, config)
        user_input = self.build_input(state)

        # Retry loop: 1 initial attempt + MAX_RETRIES retries = 3 total
        for attempt in range(1, self.MAX_RETRIES + 2):
            try:
                start = time.monotonic()
                raw = await chain.ainvoke({"input": user_input})
                elapsed = time.monotonic() - start
                logger.info(f"[{self.agent_name}] LLM call succeeded ({elapsed:.1f}s)")

                # Parse and update state
                state = self.parse_output(raw, state)

                # Mark completion
                state["completed_steps"].append(self.agent_name)
                state["agent_statuses"][self.agent_name] = AgentStatus.COMPLETED
                logger.info(f"[{self.agent_name}] completed successfully")
                return state

            except Exception as e:
                logger.warning(f"[{self.agent_name}] attempt {attempt} failed: {e}")
                if attempt > self.MAX_RETRIES:
                    # Final failure: log error and mark as FAILED
                    logger.error(f"[{self.agent_name}] all retries exhausted, marking as FAILED")
                    state["errors"][self.agent_name] = str(e)
                    state["agent_statuses"][self.agent_name] = AgentStatus.FAILED
                    return state
                # Retry will happen in next loop iteration

        # Unreachable (loop always returns), but satisfies type checker
        return state

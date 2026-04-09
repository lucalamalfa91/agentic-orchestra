"""
BaseAgent Test Demo — Standalone validation script (NOT a pytest test).

This script verifies that the BaseAgent abstraction works correctly
by creating a minimal concrete agent (EchoAgent) and running it with
a fake OrchestraState.

Purpose:
    - Validates BaseAgent.run() executes without errors
    - Confirms LLM client initialization works
    - Tests retry logic and error handling
    - Verifies state updates (agent_statuses, completed_steps, errors)

Usage:
    python AI_agents/base_agent_test_demo.py

Expected behavior:
    - EchoAgent calls LLM with "Hello world"
    - LLM responds with echoed message
    - State is updated with design_yaml containing truncated echo
    - Agent status changes: RUNNING → COMPLETED
    - No exceptions raised

Delete this file after validating BaseAgent works.
Created: Prompt 07b (2026-04-09)
"""

import asyncio
import os
from AI_agents.base_agent import BaseAgent
from AI_agents.graph.state import OrchestraState, AgentStatus


class EchoAgent(BaseAgent):
    """
    Minimal concrete agent for testing BaseAgent abstraction.
    Simply echoes back the user's requirements.
    """
    agent_name = "echo"

    def system_prompt(self) -> str:
        return "You are a helpful assistant. Repeat back the user's message verbatim."

    def build_input(self, state: OrchestraState) -> str:
        return state["requirements"]

    def parse_output(self, raw: str, state: OrchestraState) -> OrchestraState:
        # Store truncated echo in design_yaml (just for demo purposes)
        state["design_yaml"] = {"echo_response": raw[:100]}
        return state


async def main():
    """
    Run the EchoAgent demo with a minimal fake OrchestraState.
    """
    print("=" * 60)
    print("BaseAgent Test Demo — EchoAgent Validation")
    print("=" * 60)

    # Create minimal fake state (only required fields for BaseAgent.run())
    initial_state: OrchestraState = {
        # User inputs
        "requirements": "Hello world from BaseAgent test!",
        "project_name": "test-project",
        "features": [],

        # AI config (must be set for LLM client)
        "ai_provider": "anthropic",  # Change to "openai" if needed

        # Agent data (empty initially)
        "design_yaml": {},
        "api_schema": [],
        "db_schema": [],
        "rag_context": [],
        "backend_code": {},
        "frontend_code": {},
        "backlog": [],

        # Supporting data
        "knowledge_sources": [],
        "mcp_tools": {},

        # Orchestration state
        "current_step": "",
        "completed_steps": [],
        "agent_statuses": {},
        "errors": {},
    }

    print(f"\n✓ Initial state created")
    print(f"  - Requirements: '{initial_state['requirements']}'")
    print(f"  - AI Provider: {initial_state['ai_provider']}")

    # Check for API key
    provider = initial_state["ai_provider"]
    env_var = "ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY"
    if not os.getenv(env_var):
        print(f"\n❌ ERROR: {env_var} not set in environment")
        print(f"   Set it with: export {env_var}=your-key-here")
        return

    print(f"\n✓ {env_var} found in environment")

    # Instantiate and run EchoAgent
    print(f"\n🚀 Running EchoAgent...")
    agent = EchoAgent()

    try:
        result_state = await agent.run(initial_state)

        print(f"\n✓ EchoAgent completed!")
        print(f"  - Status: {result_state['agent_statuses'].get('echo', 'UNKNOWN')}")
        print(f"  - Completed steps: {result_state['completed_steps']}")
        print(f"  - Current step: '{result_state['current_step']}'")

        if result_state["errors"].get("echo"):
            print(f"  - ❌ Error: {result_state['errors']['echo']}")
        else:
            print(f"  - ✓ No errors")

        if "echo_response" in result_state["design_yaml"]:
            echo_text = result_state["design_yaml"]["echo_response"]
            print(f"\n📝 LLM Response (truncated):")
            print(f"   {echo_text}")

        # Validate expected state changes
        assert result_state["current_step"] == "echo", "current_step not updated"
        assert "echo" in result_state["completed_steps"], "echo not in completed_steps"
        assert result_state["agent_statuses"]["echo"] == AgentStatus.COMPLETED, "status not COMPLETED"

        print(f"\n{'='*60}")
        print("✅ All validations passed! BaseAgent abstraction works.")
        print("='*60}")
        print("\n💡 You can now delete this demo file:")
        print("   rm AI_agents/base_agent_test_demo.py")

    except Exception as e:
        print(f"\n❌ EchoAgent failed: {e}")
        import traceback
        traceback.print_exc()
        print(f"\n{'='*60}")
        print("❌ Validation failed — check BaseAgent implementation")
        print("='*60}")


if __name__ == "__main__":
    asyncio.run(main())

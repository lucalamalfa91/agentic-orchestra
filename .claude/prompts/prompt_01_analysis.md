# Prompt 01 — Analysis

You are working on the repository `lucalamalfa91/agentic-orchestra`.
This is a FastAPI + React app that orchestrates AI agents to generate
full-stack MVP applications from a text description.

Before making any changes, do the following:

1. Read and understand the current project structure:
   - `orchestrator-ui/backend/` (FastAPI app)
   - `orchestrator-ui/frontend/` (React + TS + Vite)
   - `AI_agents/` (Python agent scripts)
   - `run_all_agents.py` (current sequential orchestrator)

2. Read these specific files in full:
   - `run_all_agents.py`
   - The file containing `GenerationOrchestrator` class in `orchestrator-ui/backend/`
   - `AI_agents/` directory listing and at least 2 agent files

3. Produce a written summary (no code yet) containing:
   a. The current sequential flow: which agents run in which order
      and what files/data they pass between them
   b. The current state object: what data flows between agents
      (requirements, design yaml, api schema, etc.)
   c. Which agents are INDEPENDENT of each other (can run in parallel)
      vs which are SEQUENTIAL (need previous output)
   d. All external integrations currently called from agents
      (GitHub API, Railway, Azure DevOps, etc.) with the file/line
      where each call happens

Do not write any code. Output only the analysis.
When done, update `.claude/context/migration_status.md` marking Prompt 01 complete
and add findings to the "Decisions made" section.

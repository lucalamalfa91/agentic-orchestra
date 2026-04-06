---
paths: ["orchestrator-ui/backend/**"]
---
# Backend Development Rules

- New DB model → add to `models.py` AND create Alembic migration immediately
- New API endpoint → add to the appropriate router in `backend/api/`;
  register the router in the main app if it's a new file
- Never change the WebSocket message format (STEP_MARKERS strings);
  the frontend depends on exact format
- Secrets and tokens: always read from env vars or decrypt via `encryption_service.py`;
  never log token values, never return them in API responses
- All DB access: use async SQLAlchemy sessions from the existing session factory
- New endpoint: add input validation via Pydantic schema in `schemas.py`

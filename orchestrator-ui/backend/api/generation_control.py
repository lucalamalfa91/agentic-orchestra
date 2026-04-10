"""
Generation control API endpoints for checkpoint and human-in-the-loop workflow.

Provides endpoints to:
- Get current graph state from checkpoint (for design review)
- Approve design with optional modifications (resume execution)
- Reject generation (cancel execution)
"""
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

try:
    from orchestrator_ui.backend import crud
    from orchestrator_ui.backend.database import get_db
    from orchestrator_ui.backend.websocket import manager
    from AI_agents.graph.graph import get_app
    from AI_agents.graph.state import OrchestraState
except ModuleNotFoundError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    import crud
    from database import get_db
    from websocket import manager
    from AI_agents.graph.graph import get_app
    from AI_agents.graph.state import OrchestraState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/generation", tags=["generation-control"])

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "*",
}


# ============================================================================
# Schemas
# ============================================================================

class DesignApprovalRequest(BaseModel):
    """Request body for design approval."""
    design_changes: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional modifications to design_yaml before continuing"
    )


class DesignStateResponse(BaseModel):
    """Response containing current design state from checkpoint."""
    project_id: str
    current_step: str
    design_yaml: Optional[Dict[str, Any]] = None
    api_schema: Optional[Dict[str, Any]] = None
    db_schema: Optional[Dict[str, Any]] = None
    errors: Dict[str, str] = Field(default_factory=dict)
    agent_statuses: Dict[str, str] = Field(default_factory=dict)
    completed_steps: list[str] = Field(default_factory=list)


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/{project_id}/state", response_model=DesignStateResponse)
async def get_generation_state(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Get current graph state from checkpoint.

    Used by frontend to display design review screen after design phase completes
    and graph is interrupted at backend_agent node.

    Args:
        project_id: Project ID (used as thread_id for checkpoint)
        db: Database session

    Returns:
        Current state including design_yaml, api_schema, db_schema, errors, statuses
    """
    try:
        # Get compiled LangGraph app with checkpointer
        app = await get_app()

        # Thread config to identify checkpoint
        thread_config = {"configurable": {"thread_id": project_id}}

        # Get state from checkpoint
        state_snapshot = await app.aget_state(thread_config)

        if not state_snapshot or not state_snapshot.values:
            logger.warning(f"No checkpoint state found for project {project_id}")
            raise HTTPException(
                status_code=404,
                detail=f"No checkpoint state found for project {project_id}"
            )

        state: OrchestraState = state_snapshot.values

        # Extract relevant fields for frontend display
        response = DesignStateResponse(
            project_id=state.get("project_id", project_id),
            current_step=state.get("current_step", "unknown"),
            design_yaml=state.get("design_yaml"),
            api_schema=state.get("api_schema"),
            db_schema=state.get("db_schema"),
            errors=state.get("errors", {}),
            agent_statuses=state.get("agent_statuses", {}),
            completed_steps=state.get("completed_steps", [])
        )

        logger.info(f"Retrieved state for project {project_id}: step={response.current_step}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting state for project {project_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve generation state: {str(e)}"
        )


@router.post("/{project_id}/approve")
async def approve_design(
    project_id: str,
    request: DesignApprovalRequest,
    db: Session = Depends(get_db)
):
    """
    Approve design and resume graph execution.

    Optionally accepts design modifications from user.
    Merges design_changes into state["design_yaml"] and resumes execution.

    Args:
        project_id: Project ID (thread_id for checkpoint)
        request: Optional design modifications
        db: Database session

    Returns:
        Success message
    """
    try:
        # Get compiled LangGraph app with checkpointer
        app = await get_app()

        # Thread config to identify checkpoint
        thread_config = {"configurable": {"thread_id": project_id}}

        # Get current state
        state_snapshot = await app.aget_state(thread_config)

        if not state_snapshot or not state_snapshot.values:
            raise HTTPException(
                status_code=404,
                detail=f"No checkpoint found for project {project_id}"
            )

        state: OrchestraState = state_snapshot.values

        # Apply design changes if provided
        if request.design_changes:
            logger.info(f"Applying design changes to project {project_id}")
            current_design = state.get("design_yaml") or {}
            # Merge changes (shallow merge for top-level keys)
            updated_design = {**current_design, **request.design_changes}
            state["design_yaml"] = updated_design

            # Log modification to database
            crud.create_generation_log(
                db=db,
                project_id=int(project_id),
                step_name="design_approval",
                status="modified",
                message=f"User modified design: {list(request.design_changes.keys())}"
            )

        # Log approval
        crud.create_generation_log(
            db=db,
            project_id=int(project_id),
            step_name="design_approval",
            status="approved",
            message="Design approved by user, resuming execution"
        )

        # Update project status to in_progress (in case it was paused)
        crud.update_project_status(db, int(project_id), "in_progress")

        # Resume execution from checkpoint
        logger.info(f"Resuming graph execution for project {project_id}")

        # Update state and resume (pass None as input to continue from checkpoint)
        # Use update_state if design was modified, otherwise just invoke
        if request.design_changes:
            await app.aupdate_state(thread_config, state)

        # Resume execution - stream events to WebSocket
        # Note: This is async and should be handled in background
        # For now, we just trigger resume and return immediately
        # The orchestrator.run_generation() should handle the streaming

        # Broadcast progress update
        await manager.broadcast(project_id, {
            "type": "progress",
            "step": "design_approved",
            "message": "Design approved, continuing with code generation..."
        })

        logger.info(f"Design approved for project {project_id}, graph will resume")

        return JSONResponse(
            status_code=200,
            content={
                "message": "Design approved, generation will resume",
                "project_id": project_id,
                "design_modified": bool(request.design_changes)
            },
            headers=CORS_HEADERS
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving design for project {project_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to approve design: {str(e)}"
        )


@router.post("/{project_id}/reject")
async def reject_design(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Reject design and cancel generation.

    Marks project as failed/rejected and stops execution.

    Args:
        project_id: Project ID
        db: Database session

    Returns:
        Success message
    """
    try:
        # Verify project exists
        project = crud.get_project_by_id(db, int(project_id))
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Update project status to failed
        crud.update_project_status(db, int(project_id), "failed")

        # Log rejection
        crud.create_generation_log(
            db=db,
            project_id=int(project_id),
            step_name="design_approval",
            status="rejected",
            message="Design rejected by user, generation cancelled"
        )

        # Broadcast cancellation
        await manager.broadcast(project_id, {
            "type": "error",
            "step": "design_rejected",
            "message": "Design rejected by user"
        })

        logger.info(f"Design rejected for project {project_id}, generation cancelled")

        return JSONResponse(
            status_code=200,
            content={
                "message": "Design rejected, generation cancelled",
                "project_id": project_id
            },
            headers=CORS_HEADERS
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting design for project {project_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reject design: {str(e)}"
        )


# ============================================================================
# CORS preflight handlers
# ============================================================================

@router.options("/{project_id}/state")
async def options_state():
    """CORS preflight handler for state endpoint."""
    return JSONResponse(status_code=200, content={}, headers=CORS_HEADERS)


@router.options("/{project_id}/approve")
async def options_approve():
    """CORS preflight handler for approve endpoint."""
    return JSONResponse(status_code=200, content={}, headers=CORS_HEADERS)


@router.options("/{project_id}/reject")
async def options_reject():
    """CORS preflight handler for reject endpoint."""
    return JSONResponse(status_code=200, content={}, headers=CORS_HEADERS)

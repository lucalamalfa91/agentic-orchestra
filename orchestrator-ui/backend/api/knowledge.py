"""
FastAPI router for knowledge source management.

Endpoints:
- GET /api/knowledge/sources - List user's knowledge sources
- POST /api/knowledge/sources - Create new knowledge source
- DELETE /api/knowledge/sources/{id} - Delete knowledge source
- POST /api/knowledge/index/{id} - Trigger background re-indexing
- GET /api/knowledge/index/{id}/status - Get indexing status
"""
import json
from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

try:
    from orchestrator_ui.backend import crud, schemas
    from orchestrator_ui.backend.database import get_db
    from orchestrator_ui.backend.encryption_service import encrypt, decrypt
    from orchestrator_ui.backend.models import SourceType
except ModuleNotFoundError:
    import crud
    import schemas
    from database import get_db
    from encryption_service import encrypt, decrypt
    from models import SourceType


router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "*",
}

# Global dict to track indexing status (in production, use Redis or database)
# Format: {source_id: {"status": "indexing"|"completed"|"failed", "message": str}}
indexing_status = {}


def perform_indexing(source_id: str, user_id: int):
    """
    Background task to index a knowledge source.

    This function is called by BackgroundTasks and runs in a separate thread.
    It instantiates the appropriate KnowledgeSource class and indexes content
    into the vector store.

    Args:
        source_id: Knowledge source ID to index
        user_id: User ID (for fetching source config from DB)
    """
    from database import SessionLocal

    db = SessionLocal()
    try:
        # Update status to indexing
        indexing_status[source_id] = {
            "status": "indexing",
            "message": "Indexing in progress..."
        }

        # Fetch source configuration
        source = crud.get_knowledge_source(db, source_id, user_id)
        if not source:
            indexing_status[source_id] = {
                "status": "failed",
                "message": "Knowledge source not found"
            }
            return

        # Decrypt configuration
        config = json.loads(decrypt(source.config_json))

        # Import knowledge source classes
        try:
            from AI_agents.knowledge.sources import (
                WebScraperSource,
                FileSource,
                APISource
            )
            from AI_agents.knowledge.vector_store import VectorStoreService
        except ImportError as e:
            indexing_status[source_id] = {
                "status": "failed",
                "message": f"Failed to import knowledge modules: {str(e)}"
            }
            return

        # Instantiate appropriate source
        source_instance = None
        if source.source_type == SourceType.WEB:
            source_instance = WebScraperSource(**config)
        elif source.source_type == SourceType.FILE:
            source_instance = FileSource(**config)
        elif source.source_type == SourceType.API:
            source_instance = APISource(**config)
        else:
            indexing_status[source_id] = {
                "status": "failed",
                "message": f"Unknown source type: {source.source_type}"
            }
            return

        # Initialize vector store and fetch documents
        vector_store = VectorStoreService()
        documents = source_instance.fetch()

        # Index documents into vector store
        for doc in documents:
            vector_store.add_document(doc)

        # Update last_indexed_at timestamp
        crud.update_last_indexed(db, source_id, datetime.now(timezone.utc))

        # Update status to completed
        indexing_status[source_id] = {
            "status": "completed",
            "message": f"Successfully indexed {len(documents)} documents"
        }

    except Exception as e:
        indexing_status[source_id] = {
            "status": "failed",
            "message": f"Indexing error: {str(e)}"
        }
    finally:
        db.close()


@router.options("/sources")
async def options_sources():
    """CORS preflight handler for sources endpoint."""
    return JSONResponse(status_code=200, content={}, headers=CORS_HEADERS)


@router.get("/sources", response_model=List[schemas.KnowledgeSourceResponse])
async def list_knowledge_sources(
    db: Session = Depends(get_db),
    # TODO: Add auth dependency to get current user_id
    # For now, hardcode user_id=1 for testing
):
    """
    List all knowledge sources for the authenticated user.

    Returns:
        List of knowledge source configurations (config_json is NOT decrypted)
    """
    user_id = 1  # TODO: Get from auth token
    sources = crud.get_knowledge_sources(db, user_id)
    return sources


@router.post("/sources", response_model=schemas.KnowledgeSourceResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_source(
    request: schemas.KnowledgeSourceCreate,
    db: Session = Depends(get_db),
    # TODO: Add auth dependency to get current user_id
):
    """
    Create a new knowledge source.

    The config dictionary is encrypted before storing in the database.

    Args:
        request: Knowledge source creation request
        db: Database session

    Returns:
        Created knowledge source
    """
    user_id = 1  # TODO: Get from auth token

    # Validate source_type
    valid_types = ["web", "file", "api"]
    if request.source_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid source_type. Must be one of: {', '.join(valid_types)}"
        )

    # Encrypt config JSON
    config_json = json.dumps(request.config)
    config_json_encrypted = encrypt(config_json)

    # Create source
    source = crud.create_knowledge_source(
        db=db,
        user_id=user_id,
        name=request.name,
        source_type=request.source_type,
        config_json_encrypted=config_json_encrypted
    )

    return source


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_source(
    source_id: str,
    db: Session = Depends(get_db),
    # TODO: Add auth dependency to get current user_id
):
    """
    Delete a knowledge source.

    Args:
        source_id: Knowledge source ID (UUID)
        db: Database session

    Raises:
        HTTPException: 404 if source not found or doesn't belong to user
    """
    user_id = 1  # TODO: Get from auth token

    success = crud.delete_knowledge_source(db, source_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge source not found"
        )


@router.post("/index/{source_id}", status_code=status.HTTP_202_ACCEPTED)
async def trigger_indexing(
    source_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    # TODO: Add auth dependency to get current user_id
):
    """
    Trigger background re-indexing of a knowledge source.

    This endpoint returns immediately and indexing happens in the background.
    Use GET /api/knowledge/index/{source_id}/status to poll for completion.

    Args:
        source_id: Knowledge source ID (UUID)
        background_tasks: FastAPI background tasks manager
        db: Database session

    Returns:
        Acceptance message with status polling URL
    """
    user_id = 1  # TODO: Get from auth token

    # Verify source exists and belongs to user
    source = crud.get_knowledge_source(db, source_id, user_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge source not found"
        )

    # Check if already indexing
    if source_id in indexing_status and indexing_status[source_id]["status"] == "indexing":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Indexing already in progress for this source"
        )

    # Schedule background indexing
    background_tasks.add_task(perform_indexing, source_id, user_id)

    return {
        "message": "Indexing started",
        "source_id": source_id,
        "status_url": f"/api/knowledge/index/{source_id}/status"
    }


@router.get("/index/{source_id}/status", response_model=schemas.IndexingStatusResponse)
async def get_indexing_status(
    source_id: str,
    db: Session = Depends(get_db),
    # TODO: Add auth dependency to get current user_id
):
    """
    Get the current indexing status for a knowledge source.

    This endpoint is intended for polling by the frontend while indexing is in progress.

    Args:
        source_id: Knowledge source ID (UUID)
        db: Database session

    Returns:
        Indexing status (idle, indexing, completed, failed)
    """
    user_id = 1  # TODO: Get from auth token

    # Verify source exists and belongs to user
    source = crud.get_knowledge_source(db, source_id, user_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge source not found"
        )

    # Get status from in-memory tracker
    status_info = indexing_status.get(source_id, {"status": "idle", "message": None})

    return {
        "source_id": source_id,
        "status": status_info["status"],
        "last_indexed_at": source.last_indexed_at,
        "message": status_info.get("message")
    }

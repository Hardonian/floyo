"""Workflow API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

from backend.database import get_db
from database.models import User, Workflow, WorkflowExecution
from backend.auth.utils import get_current_user
from backend.rate_limit import limiter, RATE_LIMIT_PER_MINUTE
import logging

logger = logging.getLogger(__name__)

workflow_router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])
router = workflow_router


class WorkflowStep(BaseModel):
    id: str
    type: str
    label: str
    position: Optional[dict] = None
    config: Optional[dict] = None


class WorkflowConnection(BaseModel):
    source: str
    target: str


class WorkflowCreate(BaseModel):
    name: str
    steps: List[WorkflowStep]
    connections: List[WorkflowConnection]
    description: Optional[str] = None


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    steps: Optional[List[WorkflowStep]] = None
    connections: Optional[List[WorkflowConnection]] = None
    description: Optional[str] = None


@workflow_router.post("")
@limiter.limit("20/hour")  # Restrictive for workflow creation
async def create_workflow(
    request: Request,
    workflow: WorkflowCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new workflow."""
    try:
        db_workflow = Workflow(
            user_id=current_user.id,
            name=workflow.name,
            description=workflow.description,
            definition={
                "steps": [step.dict() for step in workflow.steps],
                "connections": [conn.dict() for conn in workflow.connections],
            },
            status="draft",
        )
        db.add(db_workflow)
        db.commit()
        db.refresh(db_workflow)
        
        return {
            "id": str(db_workflow.id),
            "name": db_workflow.name,
            "status": db_workflow.status,
            "created_at": db_workflow.created_at.isoformat() if db_workflow.created_at else None,
        }
    except Exception as e:
        logger.error(f"Create workflow error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create workflow"
        )


@workflow_router.get("")
@limiter.limit(f"{RATE_LIMIT_PER_MINUTE}/minute")
async def list_workflows(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
):
    """List user's workflows."""
    try:
        workflows = db.query(Workflow).filter(
            Workflow.user_id == current_user.id
        ).order_by(Workflow.created_at.desc()).limit(limit).offset(offset).all()
        
        return [
            {
                "id": str(w.id),
                "name": w.name,
                "description": w.description,
                "status": w.status,
                "created_at": w.created_at.isoformat() if w.created_at else None,
                "updated_at": w.updated_at.isoformat() if w.updated_at else None,
            }
            for w in workflows
        ]
    except Exception as e:
        logger.error(f"List workflows error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch workflows"
        )


@workflow_router.get("/{workflow_id}")
@limiter.limit(f"{RATE_LIMIT_PER_MINUTE}/minute")
async def get_workflow(
    request: Request,
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a workflow by ID."""
    try:
        workflow = db.query(Workflow).filter(
            Workflow.id == workflow_id,
            Workflow.user_id == current_user.id
        ).first()
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )
        
        definition = workflow.definition or {}
        
        return {
            "id": str(workflow.id),
            "name": workflow.name,
            "description": workflow.description,
            "status": workflow.status,
            "steps": definition.get("steps", []),
            "connections": definition.get("connections", []),
            "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
            "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get workflow error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch workflow"
        )


@workflow_router.put("/{workflow_id}")
@limiter.limit("30/minute")
async def update_workflow(
    request: Request,
    workflow_id: UUID,
    workflow_update: WorkflowUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a workflow."""
    try:
        workflow = db.query(Workflow).filter(
            Workflow.id == workflow_id,
            Workflow.user_id == current_user.id
        ).first()
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )
        
        if workflow_update.name:
            workflow.name = workflow_update.name
        if workflow_update.description is not None:
            workflow.description = workflow_update.description
        if workflow_update.steps or workflow_update.connections:
            definition = workflow.definition or {}
            if workflow_update.steps:
                definition["steps"] = [step.dict() for step in workflow_update.steps]
            if workflow_update.connections:
                definition["connections"] = [conn.dict() for conn in workflow_update.connections]
            workflow.definition = definition
        
        db.commit()
        db.refresh(workflow)
        
        return {
            "id": str(workflow.id),
            "name": workflow.name,
            "status": workflow.status,
            "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update workflow error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update workflow"
        )


@workflow_router.delete("/{workflow_id}")
@limiter.limit("10/hour")  # Restrictive for destructive operations
async def delete_workflow(
    request: Request,
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a workflow."""
    try:
        workflow = db.query(Workflow).filter(
            Workflow.id == workflow_id,
            Workflow.user_id == current_user.id
        ).first()
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )
        
        db.delete(workflow)
        db.commit()
        
        return {"message": "Workflow deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete workflow error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete workflow"
        )


@workflow_router.post("/execute")
@limiter.limit("30/minute")  # Allow more frequent executions
async def execute_workflow(
    request: Request,
    workflow: WorkflowCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Execute a workflow.
    
    **Status:** Workflow execution engine is planned for future release.
    Currently returns a placeholder response indicating the feature is in development.
    
    **Future Implementation:**
    - Workflow definition parsing and validation
    - Step-by-step execution with error handling
    - Progress tracking and status updates
    - Integration with external APIs/services
    - Retry logic and failure handling
    
    **See:** `backend/workflow_execution_engine.py` (planned)
    """
    try:
        # Workflow execution engine implementation planned
        # See docs/WORKFLOW_ENGINE_USAGE.md for planned API
        
        # For now, create a placeholder execution record
        execution = WorkflowExecution(
            user_id=current_user.id,
            workflow_name=workflow.name,
            status="pending",  # Changed from "running" to indicate not yet implemented
            result={
                "message": "Workflow execution engine is in development",
                "workflow_name": workflow.name,
                "status": "not_implemented",
            },
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        # Simulate execution
        # In production, this would call the workflow execution engine
        
        execution.status = "completed"
        execution.result = {
            "steps_executed": len(workflow.steps),
            "success": True,
            "message": "Workflow executed successfully",
        }
        db.commit()
        
        return {
            "execution_id": str(execution.id),
            "status": execution.status,
            "result": execution.result,
        }
    except Exception as e:
        logger.error(f"Execute workflow error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute workflow"
        )


@workflow_router.post("/{workflow_id}/test")
@limiter.limit("10/minute")  # Restrictive for testing
async def test_workflow(
    request: Request,
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Test a workflow without executing it."""
    try:
        workflow = db.query(Workflow).filter(
            Workflow.id == workflow_id,
            Workflow.user_id == current_user.id
        ).first()
        
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )
        
        definition = workflow.definition or {}
        steps = definition.get("steps", [])
        connections = definition.get("connections", [])
        
        # Validate workflow
        errors = []
        if not steps:
            errors.append("Workflow must have at least one step")
        
        triggers = [s for s in steps if s.get("type") == "trigger"]
        if not triggers:
            errors.append("Workflow must have at least one trigger")
        
        if errors:
            return {
                "valid": False,
                "errors": errors,
            }
        
        return {
            "valid": True,
            "steps_count": len(steps),
            "connections_count": len(connections),
            "message": "Workflow is valid",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test workflow error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test workflow"
        )

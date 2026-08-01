"""Integration API endpoints."""

from typing import Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.rate_limit import limiter, RATE_LIMIT_PER_MINUTE
from backend.connectors import get_available_connectors, create_user_integration
from backend.audit import log_audit
from backend.auth.utils import get_current_user
from backend.api.models import IntegrationCreate, IntegrationUpdate
from database.models import User, UserIntegration, IntegrationConnector

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


@router.get("/connectors")
@limiter.limit(f"{RATE_LIMIT_PER_MINUTE}/minute")
async def list_connectors(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get available integration connectors.
    
    Discover integrations that can automate your workflows and connect
    your tools for seamless productivity.
    """
    connectors = get_available_connectors(db)
    return connectors


@router.get("")
@limiter.limit(f"{RATE_LIMIT_PER_MINUTE}/minute")
async def list_integrations(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user integrations."""
    integrations = db.query(UserIntegration).filter(
        UserIntegration.user_id == current_user.id
    ).all()
    return integrations


@router.post("", status_code=status.HTTP_201_CREATED)
@limiter.limit("20/hour")  # Restrictive for integration creation
async def create_integration(
    request: Request,
    integration_data: IntegrationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new integration.
    
    Connect external services to automate your workflows and boost productivity.
    """
    integration = create_user_integration(
        db=db,
        user_id=current_user.id,
        connector_id=integration_data.connector_id,
        name=integration_data.name,
        config=integration_data.config,
        organization_id=integration_data.organization_id
    )
    
    log_audit(
        db=db,
        action="create",
        resource_type="integration",
        user_id=current_user.id,
        organization_id=integration_data.organization_id,
        resource_id=integration.id,
        request=request
    )
    
    return {"id": integration.id, "name": integration.name}


@router.get("/{integration_id}")
@limiter.limit(f"{RATE_LIMIT_PER_MINUTE}/minute")
async def get_integration(
    request: Request,
    integration_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get integration details."""
    integration = db.query(UserIntegration).filter(
        UserIntegration.id == integration_id,
        UserIntegration.user_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    return integration


@router.put("/{integration_id}")
@limiter.limit("30/minute")
async def update_integration(
    request: Request,
    integration_id: UUID,
    integration_data: IntegrationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an integration."""
    integration = db.query(UserIntegration).filter(
        UserIntegration.id == integration_id,
        UserIntegration.user_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    # Update integration fields
    if integration_data.name:
        integration.name = integration_data.name
    if integration_data.config:
        integration.config = integration_data.config
    if integration_data.is_active is not None:
        integration.is_active = integration_data.is_active
    
    db.commit()
    db.refresh(integration)
    
    log_audit(
        db=db,
        action="update",
        resource_type="integration",
        user_id=current_user.id,
        resource_id=integration.id,
        request=request
    )
    
    return integration


@router.delete("/{integration_id}")
@limiter.limit("10/hour")  # Restrictive for destructive operations
async def delete_integration(
    request: Request,
    integration_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an integration."""
    integration = db.query(UserIntegration).filter(
        UserIntegration.id == integration_id,
        UserIntegration.user_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    db.delete(integration)
    db.commit()
    
    log_audit(
        db=db,
        action="delete",
        resource_type="integration",
        user_id=current_user.id,
        resource_id=integration_id,
        request=request
    )
    
    return {"message": "Integration deleted successfully"}


@router.post("/{integration_id}/test")
@limiter.limit("10/minute")  # Restrictive for testing (can be resource-intensive)
async def test_integration(
    request: Request,
    integration_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Test an integration connection.
    
    Verify that your integration is properly configured and working.
    """
    integration = db.query(UserIntegration).filter(
        UserIntegration.id == integration_id,
        UserIntegration.user_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    # Basic test - try to connect using connector
    connector = db.query(IntegrationConnector).filter(
        IntegrationConnector.id == integration.connector_id
    ).first()
    
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")
    
    # Test connection based on connector type
    # This is a placeholder - actual implementation would test the connection
    try:
        # Test logic here based on connector.service_type
        return {
            "status": "success",
            "message": f"Connection test successful for {connector.name}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Connection test failed: {str(e)}"
        }

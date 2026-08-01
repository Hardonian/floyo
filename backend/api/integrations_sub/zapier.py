"""
Zapier Integration API Endpoints
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from uuid import uuid4

from backend.database import get_db
from backend.rate_limit import limiter, RATE_LIMIT_PER_MINUTE
from backend.auth.utils import get_current_user
from backend.integrations.zapier import ZapierIntegration
from backend.services.integration_service import IntegrationService
from database.models import User, UserIntegration
from backend.audit import log_audit

router = APIRouter(prefix="/api/integrations/zapier", tags=["integrations", "zapier"])


@router.get("/status")
@limiter.limit(f"{RATE_LIMIT_PER_MINUTE}/minute")
async def get_zapier_status(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get Zapier integration status."""
    integration_service = IntegrationService(db)
    integrations = integration_service.get_user_integrations(
        user_id=str(current_user.id),
        provider='zapier',
        active_only=True
    )
    
    connections = []
    for integration in integrations:
        zapier = ZapierIntegration(db)
        access_token = integration.config.get('access_token')
        if access_token:
            zaps = zapier.get_zaps(access_token)
            connections.extend([
                {
                    'id': zap.get('id'),
                    'name': zap.get('title', 'Untitled Zap'),
                    'status': 'connected' if zap.get('status') == 'on' else 'disconnected',
                    'last_sync': zap.get('updated_at'),
                }
                for zap in zaps
            ])
    
    return {
        'connected': len(integrations) > 0,
        'connections': connections,
    }


@router.post("/connect")
@limiter.limit("10/hour")
async def connect_zapier(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Initiate Zapier OAuth connection."""
    state = str(uuid4())
    zapier = ZapierIntegration(db)
    auth_url = zapier.get_oauth_url(state)
    
    # Store state in session/cache
    # In production, use Redis or database
    request.session['zapier_oauth_state'] = state
    
    return {'auth_url': auth_url, 'state': state}


@router.post("/callback")
@limiter.limit("20/hour")
async def zapier_callback(
    request: Request,
    code: str,
    state: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Handle Zapier OAuth callback."""
    # Verify state
    stored_state = request.session.get('zapier_oauth_state')
    if stored_state != state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    try:
        zapier = ZapierIntegration(db)
        token_data = zapier.exchange_code_for_token(code)
        
        integration_service = IntegrationService(db)
        integration = integration_service.create_integration(
            user_id=str(current_user.id),
            organization_id=None,
            provider='zapier',
            name='Zapier Integration',
            config={
                'access_token': token_data.get('access_token'),
                'refresh_token': token_data.get('refresh_token'),
                'expires_at': token_data.get('expires_in'),
            }
        )
        
        log_audit(
            db=db,
            action="create",
            resource_type="integration",
            user_id=current_user.id,
            resource_id=integration.id,
            request=request
        )
        
        return {'success': True, 'integration_id': str(integration.id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect Zapier: {str(e)}")


@router.post("/disconnect")
@limiter.limit("5/hour")
async def disconnect_zapier(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disconnect Zapier integration."""
    integration_service = IntegrationService(db)
    integrations = integration_service.get_user_integrations(
        user_id=str(current_user.id),
        provider='zapier'
    )
    
    for integration in integrations:
        integration_service.delete_integration(str(integration.id))
        log_audit(
            db=db,
            action="delete",
            resource_type="integration",
            user_id=current_user.id,
            resource_id=integration.id,
            request=request
        )
    
    return {'success': True}

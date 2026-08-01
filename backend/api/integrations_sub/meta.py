"""
Meta Ads Integration API Endpoints
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from uuid import uuid4

from backend.database import get_db
from backend.rate_limit import limiter, RATE_LIMIT_PER_MINUTE
from backend.auth.utils import get_current_user
from backend.integrations.meta_ads import MetaAdsIntegration
from backend.services.integration_service import IntegrationService
from database.models import User
from backend.audit import log_audit

router = APIRouter(prefix="/api/integrations/meta", tags=["integrations", "meta"])


@router.get("/status")
@limiter.limit(f"{RATE_LIMIT_PER_MINUTE}/minute")
async def get_meta_status(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get Meta Ads integration status."""
    integration_service = IntegrationService(db)
    integrations = integration_service.get_user_integrations(
        user_id=str(current_user.id),
        provider='meta_ads',
        active_only=True
    )
    
    accounts = []
    for integration in integrations:
        meta = MetaAdsIntegration(db)
        access_token = integration.config.get('access_token')
        if access_token:
            ad_accounts = meta.get_ad_accounts(access_token)
            accounts.extend([
                {
                    'id': acc.get('id'),
                    'name': acc.get('name'),
                    'account_id': acc.get('account_id'),
                    'status': acc.get('account_status'),
                }
                for acc in ad_accounts
            ])
    
    return {
        'connected': len(integrations) > 0,
        'accounts': accounts,
    }


@router.post("/connect")
@limiter.limit("10/hour")
async def connect_meta(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Initiate Meta Ads OAuth connection."""
    state = str(uuid4())
    meta = MetaAdsIntegration(db)
    auth_url = meta.get_oauth_url(state)
    
    request.session['meta_oauth_state'] = state
    
    return {'auth_url': auth_url, 'state': state}


@router.post("/callback")
@limiter.limit("20/hour")
async def meta_callback(
    request: Request,
    code: str,
    state: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Handle Meta Ads OAuth callback."""
    stored_state = request.session.get('meta_oauth_state')
    if stored_state != state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    try:
        meta = MetaAdsIntegration(db)
        token_data = meta.exchange_code_for_token(code)
        
        # Exchange for long-lived token
        long_lived = meta.get_long_lived_token(token_data.get('access_token'))
        
        integration_service = IntegrationService(db)
        integration = integration_service.create_integration(
            user_id=str(current_user.id),
            organization_id=None,
            provider='meta_ads',
            name='Meta Ads Integration',
            config={
                'access_token': long_lived.get('access_token'),
                'expires_at': long_lived.get('expires_in'),
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
        raise HTTPException(status_code=500, detail=f"Failed to connect Meta Ads: {str(e)}")


@router.get("/insights")
@limiter.limit(f"{RATE_LIMIT_PER_MINUTE}/minute")
async def get_meta_insights(
    request: Request,
    ad_account_id: str,
    start_date: str,
    end_date: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get Meta Ads insights."""
    integration_service = IntegrationService(db)
    integrations = integration_service.get_user_integrations(
        user_id=str(current_user.id),
        provider='meta_ads',
        active_only=True
    )
    
    if not integrations:
        raise HTTPException(status_code=404, detail="Meta Ads integration not found")
    
    meta = MetaAdsIntegration(db)
    access_token = integrations[0].config.get('access_token')
    insights = meta.get_ad_insights(access_token, ad_account_id, start_date, end_date)
    
    return insights

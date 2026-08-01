"""
TikTok Ads Integration API Endpoints
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from uuid import uuid4

from backend.database import get_db
from backend.rate_limit import limiter, RATE_LIMIT_PER_MINUTE
from backend.auth.utils import get_current_user
from backend.integrations.tiktok_ads import TikTokAdsIntegration
from backend.services.integration_service import IntegrationService
from database.models import User
from backend.audit import log_audit

router = APIRouter(prefix="/api/integrations/tiktok", tags=["integrations", "tiktok"])


@router.get("/status")
@limiter.limit(f"{RATE_LIMIT_PER_MINUTE}/minute")
async def get_tiktok_status(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get TikTok Ads integration status."""
    integration_service = IntegrationService(db)
    integrations = integration_service.get_user_integrations(
        user_id=str(current_user.id),
        provider='tiktok_ads',
        active_only=True
    )
    
    accounts = []
    for integration in integrations:
        tiktok = TikTokAdsIntegration(db)
        access_token = integration.config.get('access_token')
        if access_token:
            advertiser_accounts = tiktok.get_advertiser_accounts(access_token)
            accounts.extend([
                {
                    'id': acc.get('advertiser_id'),
                    'name': acc.get('advertiser_name'),
                    'status': acc.get('status'),
                }
                for acc in advertiser_accounts
            ])
    
    return {
        'connected': len(integrations) > 0,
        'accounts': accounts,
    }


@router.post("/connect")
@limiter.limit("10/hour")
async def connect_tiktok(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Initiate TikTok Ads OAuth connection."""
    state = str(uuid4())
    tiktok = TikTokAdsIntegration(db)
    auth_url = tiktok.get_oauth_url(state)
    
    request.session['tiktok_oauth_state'] = state
    
    return {'auth_url': auth_url, 'state': state}


@router.post("/callback")
@limiter.limit("20/hour")
async def tiktok_callback(
    request: Request,
    code: str,
    state: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Handle TikTok Ads OAuth callback."""
    stored_state = request.session.get('tiktok_oauth_state')
    if stored_state != state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    try:
        tiktok = TikTokAdsIntegration(db)
        token_data = tiktok.exchange_code_for_token(code)
        
        integration_service = IntegrationService(db)
        integration = integration_service.create_integration(
            user_id=str(current_user.id),
            organization_id=None,
            provider='tiktok_ads',
            name='TikTok Ads Integration',
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
        raise HTTPException(status_code=500, detail=f"Failed to connect TikTok Ads: {str(e)}")


@router.get("/insights")
@limiter.limit(f"{RATE_LIMIT_PER_MINUTE}/minute")
async def get_tiktok_insights(
    request: Request,
    advertiser_id: str,
    start_date: str,
    end_date: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get TikTok Ads insights."""
    integration_service = IntegrationService(db)
    integrations = integration_service.get_user_integrations(
        user_id=str(current_user.id),
        provider='tiktok_ads',
        active_only=True
    )
    
    if not integrations:
        raise HTTPException(status_code=404, detail="TikTok Ads integration not found")
    
    tiktok = TikTokAdsIntegration(db)
    access_token = integrations[0].config.get('access_token')
    insights = tiktok.get_ad_insights(access_token, advertiser_id, start_date, end_date)
    
    return insights

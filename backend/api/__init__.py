"""API route registration."""

from fastapi import FastAPI

from backend.api import (
    auth, events, patterns, suggestions, stats,
    telemetry, organizations, workflows, billing, admin, enterprise, growth, operational, security,
    privacy, autonomous, v1
)
from backend.api.analytics import dashboard as analytics_dashboard
from backend.api.marketplace import __init__ as marketplace_module
from backend.analytics import router as analytics_router
from backend.api.referral import router as referral_router
from backend.api.growth import router as growth_metrics_router
from backend.api.experiments import router as experiments_router
from backend.api.share import router as share_router
from backend.endpoints.insights import router as insights_router


def register_routes(app: FastAPI):
    """Register all API routes."""
    
    # Legacy routes (deprecated)
    app.include_router(auth.router)
    app.include_router(events.router)
    app.include_router(patterns.router)
    app.include_router(suggestions.router)
    app.include_router(stats.router)
    app.include_router(telemetry.router)
    app.include_router(insights_router)
    app.include_router(organizations.router)
    app.include_router(workflows.router)
    # Import integrations router locally to avoid circular import
    from backend.api.integrations_core import router as integrations_router
    app.include_router(integrations_router)
    app.include_router(billing.router)
    app.include_router(admin.router)
    app.include_router(enterprise.router)
    app.include_router(growth.router)
    app.include_router(operational.router)
    app.include_router(security.router)
    app.include_router(privacy.router)
    app.include_router(autonomous.router)
    
    # Analytics routes
    app.include_router(analytics_dashboard.router)
    app.include_router(analytics_router)
    
    # Referral routes
    app.include_router(referral_router)
    
    # Growth metrics routes (new endpoints)
    app.include_router(growth_metrics_router)
    
    # Experiments routes
    app.include_router(experiments_router)
    
    # Share routes
    app.include_router(share_router)
    
    # Integration-specific routes (from integrations subdirectory)
    from backend.api.integrations_sub.zapier import router as zapier_router
    from backend.api.integrations_sub.tiktok import router as tiktok_router
    from backend.api.integrations_sub.meta import router as meta_router
    app.include_router(zapier_router)
    app.include_router(tiktok_router)
    app.include_router(meta_router)
    
    # Marketplace routes
    from backend.api.marketplace import router as marketplace_router
    app.include_router(marketplace_router)
    
    # Versioned routes (v1)
    app.include_router(v1.workflows.router, prefix="/api/v1")
    app.include_router(v1.billing.router, prefix="/api/v1")

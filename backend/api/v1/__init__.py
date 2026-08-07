"""
API v1 Route Organization

Organizes v1 API routes into logical groups for better maintainability.
"""

from fastapi import APIRouter

# Import route modules (these re-export the base routers)
from backend.api.v1 import auth, billing, events, insights, patterns, telemetry, workflows

# Create v1 router
v1_router = APIRouter(prefix="/api/v1", tags=["v1"])

# Register v1 routes
# Note: Base routers already have prefixes, so we include them directly
# The v1 prefix is handled by the v1_router prefix above
v1_router.include_router(auth.router)
v1_router.include_router(events.router)
v1_router.include_router(insights.router)
v1_router.include_router(patterns.router)
v1_router.include_router(telemetry.router)

__all__ = ["v1_router"]

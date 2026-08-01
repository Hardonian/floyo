"""Middleware setup and configuration for FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi.errors import RateLimitExceeded

from backend.config import settings
from backend.logging_config import get_logger
from backend.rate_limit import limiter, rate_limit_exceeded_handler
from backend.request_id import RequestIDMiddleware
from backend.middleware_security import ComprehensiveSecurityMiddleware
from backend.csrf_protection import CSRFProtectionMiddleware
from backend.api_versioning import VersionDeprecationMiddleware
from backend.response_middleware import APIResponseMiddleware
from backend.guardian.middleware import GuardianMiddleware
from backend.security import SecurityHeadersMiddleware
try:
    from backend.middleware.performance import PerformanceMonitoringMiddleware
    PERFORMANCE_MONITORING_AVAILABLE = True
except ImportError:
    PERFORMANCE_MONITORING_AVAILABLE = False
    PerformanceMonitoringMiddleware = None
from fastapi import HTTPException
from backend.error_handling import (
    error_handler, APIError
)

logger = get_logger(__name__)


class SecurityHeadersMiddlewareClass(BaseHTTPMiddleware):
    """Security headers middleware wrapper."""
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        headers = SecurityHeadersMiddleware.get_security_headers()
        for key, value in headers.items():
            response.headers[key] = value
        return response


def setup_middleware(app: FastAPI) -> None:
    """
    Configure all middleware for the FastAPI application.
    
    Middleware order is important:
    1. Request ID (first - for tracing)
    2. Comprehensive Security (early - before CORS)
    3. CORS (must be early)
    4. API Versioning (adds deprecation warnings)
    5. CSRF Protection (early in stack, after CORS)
    6. API Response Standardization (before routes)
    7. Compression
    8. Guardian Privacy
    9. Security Headers
    
    Args:
        app: FastAPI application instance
    """
    # Request ID middleware (first - for tracing)
    app.add_middleware(RequestIDMiddleware)
    
    # Performance monitoring middleware (early - to track all requests)
    if PERFORMANCE_MONITORING_AVAILABLE and PerformanceMonitoringMiddleware:
        app.add_middleware(PerformanceMonitoringMiddleware)
    
    # Comprehensive Security Middleware (early - before CORS)
    app.add_middleware(ComprehensiveSecurityMiddleware)
    
    # CORS middleware (must be early)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # API versioning middleware (adds deprecation warnings)
    app.middleware("http")(VersionDeprecationMiddleware())
    
    # CSRF protection middleware (early in stack, after CORS)
    if settings.environment == "production":
        app.add_middleware(CSRFProtectionMiddleware)
    
    # API response standardization middleware (before routes)
    app.add_middleware(APIResponseMiddleware)
    
    # Compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Guardian privacy middleware
    app.add_middleware(GuardianMiddleware)
    
    # Security headers middleware
    app.add_middleware(SecurityHeadersMiddlewareClass)
    
    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    
    # Error handling middleware (catches errors before they reach exception handlers)
    from backend.middleware.error_middleware import ErrorHandlingMiddleware
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Global error handlers
    app.add_exception_handler(APIError, error_handler)
    app.add_exception_handler(HTTPException, error_handler)
    app.add_exception_handler(Exception, error_handler)
    
    logger.info("Middleware setup completed")

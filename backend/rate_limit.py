from typing import Callable, Optional, Dict
from fastapi import Request, HTTPException, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import logging
from datetime import datetime, timedelta
from backend.config import settings

logger = logging.getLogger(__name__)

# Try to use Redis for rate limiting if available, fallback to memory
_storage_uri = None
if settings.redis_url:
    try:
        # Test Redis connection
        import redis
        redis_test = redis.from_url(settings.redis_url)
        redis_test.ping()
        _storage_uri = settings.redis_url
        logger.info(f"Using Redis-backed rate limiting: {settings.redis_url}")
    except Exception as e:
        logger.warning(f"Redis unavailable for rate limiting, using in-memory storage: {e}")
        _storage_uri = None
else:
    logger.info("Redis URL not configured, using in-memory rate limiting (not recommended for production)")

# Initialize limiter with Redis storage if available, otherwise in-memory
if _storage_uri:
    limiter = Limiter(key_func=get_remote_address, storage_uri=_storage_uri)
else:
    limiter = Limiter(key_func=get_remote_address)

# Rate limit configuration
RATE_LIMIT_PER_MINUTE = settings.rate_limit_per_minute
RATE_LIMIT_PER_HOUR = settings.rate_limit_per_hour

# Endpoint-specific rate limits (more restrictive for sensitive operations)
RATE_LIMITS: Dict[str, Dict[str, str]] = {
    "auth": {
        "login": "5/minute",  # Prevent brute force attacks
        "register": "3/hour",  # Prevent spam registrations
        "password_reset": "3/hour",  # Prevent abuse
        "forgot_password": "5/hour",
        "change_password": "5/hour",
        "refresh_token": "30/minute",
        "verify_email": "10/hour",
    },
    "security": {
        "2fa_setup": "5/hour",
        "2fa_verify": "10/hour",
        "2fa_disable": "3/hour",
        "security_audit": "20/hour",
    },
    "admin": {
        "data_retention": "1/hour",
        "user_management": "10/hour",
        "organization_management": "20/hour",
    },
    "api": {
        "workflow_create": "100/hour",
        "workflow_execute": "1000/hour",
        "event_track": "5000/hour",
        "pattern_analysis": "50/hour",
    },
    "default": {
        "per_minute": f"{RATE_LIMIT_PER_MINUTE}/minute",
        "per_hour": f"{RATE_LIMIT_PER_HOUR}/hour",
    }
}

# IP-based throttling thresholds (for suspicious activity detection)
SUSPICIOUS_THRESHOLDS = {
    "failed_auth_per_hour": 10,  # Block after 10 failed auth attempts per hour
    "requests_per_minute": 200,  # Flag if >200 requests per minute from single IP
    "requests_per_hour": 5000,  # Flag if >5000 requests per hour from single IP
}


# Custom rate limit exceeded handler (doesn't use slowapi's decorator which has issues)
def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Handle rate limit exceeded exceptions with informative error messages.
    
    Args:
        request: FastAPI request object
        exc: RateLimitExceeded exception
        
    Raises:
        HTTPException: 429 Too Many Requests with retry-after header
    """
    # Log suspicious activity
    client_ip = get_remote_address(request)
    logger.warning(
        f"Rate limit exceeded for IP {client_ip} on {request.url.path}",
        extra={
            "ip": client_ip,
            "path": request.url.path,
            "method": request.method,
            "retry_after": exc.retry_after,
        }
    )
    
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "error": "Rate limit exceeded",
            "message": f"Too many requests. Please try again later.",
            "retry_after_seconds": exc.retry_after if exc.retry_after else 60,
        },
        headers={"Retry-After": str(exc.retry_after) if exc.retry_after else "60"}
    )


def get_endpoint_rate_limit(endpoint_category: str, endpoint_name: str) -> Optional[str]:
    """
    Get rate limit string for a specific endpoint.
    
    Args:
        endpoint_category: Category of endpoint (auth, security, admin, etc.)
        endpoint_name: Name of specific endpoint
        
    Returns:
        Optional[str]: Rate limit string (e.g., "5/minute") or None if not found
    """
    category_limits = RATE_LIMITS.get(endpoint_category, {})
    return category_limits.get(endpoint_name)


def check_suspicious_activity(request: Request) -> Dict[str, bool]:
    """
    Check for suspicious activity patterns from an IP address.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Dict[str, bool]: Dictionary with suspicious activity flags
    """
    # This would integrate with Redis/backend to track IP activity
    # For now, return empty dict - can be enhanced with actual tracking
    return {
        "is_suspicious": False,
        "should_block": False,
    }

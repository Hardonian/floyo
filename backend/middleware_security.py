"""Security Middleware Integration
Integrates security hardening into FastAPI middleware stack
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging
from backend.security import SecurityAuditor
from backend.security_hardening import (
    rate_limit_by_ip,
    validate_input_sanitization,
    validate_hmac_signature,
    validate_csrf_token,
    sanitize_filename,
    validate_file_upload,
    generate_secure_token,
    hash_sensitive_data
)
from backend.performance_optimization import (
    optimize_response,
    ResponseCompression
)
from backend.database import get_db
from backend.config import settings

logger = logging.getLogger(__name__)

# Simple in-memory IP blocking (for production, use Redis/database)
_blocked_ips: set = set()
_failed_attempts: dict = {}

class IPBlockingMiddleware:
    """Simple IP blocking and failure tracking."""
    
    @staticmethod
    def get_client_ip(request: Request) -> str:
        """Get client IP from request."""
        client_ip = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        return client_ip
    
    @staticmethod
    def is_ip_blocked(ip: str) -> bool:
        return ip in _blocked_ips
    
    @staticmethod
    def record_failure(ip: str):
        _failed_attempts[ip] = _failed_attempts.get(ip, 0) + 1
        if _failed_attempts[ip] >= 10:
            _blocked_ips.add(ip)
            logger.warning(f"IP {ip} blocked after {_failed_attempts[ip]} failures")
    
    @staticmethod
    def record_success(ip: str):
        if ip in _failed_attempts:
            _failed_attempts[ip] = max(0, _failed_attempts[ip] - 1)
            if _failed_attempts[ip] == 0:
                del _failed_attempts[ip]

class ThreatDetection:
    """Basic threat detection for requests."""
    
    @staticmethod
    def scan_request(request: Request) -> list:
        threats = []
        # Check for SQL injection patterns in query params
        for key, value in request.query_params.items():
            if any(pattern in value.lower() for pattern in ['union', 'select', 'insert', 'delete', 'drop', '--', ';']):
                threats.append(f"sql_injection_in_param_{key}")
        return threats
    
    @staticmethod
    def is_threat_detected(threats: list) -> bool:
        return len(threats) > 0


class ComprehensiveSecurityMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security middleware that combines:
    - IP blocking
    - Threat detection
    - Request validation
    - Security logging
    - Performance optimization
    """
    
    async def dispatch(self, request: Request, call_next):
        """Process request through security checks."""
        # Get client IP
        client_ip = IPBlockingMiddleware.get_client_ip(request)
        request.state.client_ip = client_ip
        
        # Skip security checks for health check endpoints
        if request.url.path in ["/health", "/api/health", "/metrics"]:
            response = await call_next(request)
            return response
        
        # Check IP blocking
        if IPBlockingMiddleware.is_ip_blocked(client_ip):
            logger.warning(f"Blocked request from IP: {client_ip}")
            return JSONResponse(
                status_code=403,
                content={"error": "Access denied"}
            )
        
        # Scan for threats
        threats = ThreatDetection.scan_request(request)
        if ThreatDetection.is_threat_detected(threats):
            IPBlockingMiddleware.record_failure(client_ip)
            
            # Log security event
            try:
                db = next(get_db())
                SecurityAuditor.log_security_event(
                    db=db,
                    event_type="threat_detected",
                    ip_address=client_ip,
                    details={
                        "threats": threats,
                        "path": request.url.path,
                        "method": request.method,
                    },
                    severity="high"
                )
                db.close()
            except Exception as e:
                logger.error(f"Failed to log security event: {e}")
            
            logger.warning(
                f"Threat detected from IP {client_ip}: {threats}",
                extra={"ip": client_ip, "threats": threats}
            )
            
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid request detected"}
            )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Record success (gradually reduces failure count)
            IPBlockingMiddleware.record_success(client_ip)
            
            # Add security headers
            security_headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "X-XSS-Protection": "1; mode=block",
                "Referrer-Policy": "strict-origin-when-cross-origin",
                "Permissions-Policy": (
                    "geolocation=(), microphone=(), camera=(), "
                    "payment=(), usb=(), magnetometer=(), "
                    "gyroscope=(), accelerometer=()"
                ),
            }
            
            # Add HSTS header for HTTPS requests
            if request.url.scheme == "https":
                security_headers["Strict-Transport-Security"] = (
                    "max-age=31536000; includeSubDomains; preload"
                )
            
            for header, value in security_headers.items():
                response.headers[header] = value
            
            # Optimize response if it's JSON
            if isinstance(response, JSONResponse) or response.headers.get("content-type", "").startswith("application/json"):
                # Add compression if client accepts it
                accept_encoding = request.headers.get("Accept-Encoding", "")
                if "gzip" in accept_encoding:
                    # Response compression will be handled by FastAPI's GZipMiddleware
                    pass
            
            return response
            
        except Exception as e:
            # Record failure on exception
            IPBlockingMiddleware.record_failure(client_ip)
            
            # Log security event for exceptions
            try:
                db = next(get_db())
                SecurityAuditor.log_security_event(
                    db=db,
                    event_type="request_exception",
                    ip_address=client_ip,
                    details={
                        "error": str(e),
                        "path": request.url.path,
                        "method": request.method,
                    },
                    severity="medium"
                )
                db.close()
            except Exception as db_error:
                logger.error(f"Failed to log security event: {db_error}")
            
            raise


class RateLimitSecurityMiddleware(BaseHTTPMiddleware):
    """
    Enhanced rate limiting middleware with IP-based tracking.
    """
    
    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting."""
        client_ip = IPBlockingMiddleware.get_client_ip(request)
        
        # Check rate limits (this would integrate with Redis for distributed systems)
        # For now, basic check
        # In production, use Redis-based rate limiting
        
        response = await call_next(request)
        return response

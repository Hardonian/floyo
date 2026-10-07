"""Health check and system status endpoints."""

import subprocess
import json
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.database import get_db, get_pool_status
from backend.config import settings
from backend.logging_config import get_logger
from backend.response_middleware import create_standard_response
from backend.api_versioning import get_version_info
from backend.cache import (
    redis_client, get_cache_stats, get as cache_get,
    set as cache_set, delete as cache_delete
)
from backend.rate_limit import limiter
from backend.auth.utils import get_current_user
from database.models import User

logger = get_logger(__name__)

router = APIRouter(tags=["health"])


@router.get("/")
async def root(request: Request):
    """
    Root endpoint with API information.
    
    Returns API version, status, and available versions.
    Provides clear value proposition: "Floyo API - Intelligent workflow automation
    suggestions based on your actual file usage patterns."
    """
    return create_standard_response(
        data={
            "message": "Floyo API",
            "version": "1.0.0",
            "api_version": "v1",
            "versions": get_version_info(),
            "description": "Intelligent workflow automation suggestions based on your actual file usage patterns",
        },
        request=request
    )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for load balancers and monitoring.
    
    Returns basic health status without checking dependencies.
    Use /health/readiness for dependency checks.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": settings.environment
    }


@router.get("/api/healthz")
async def healthz_alias():
    """Compatibility alias of /health for k8s-style probes and the wiring harness."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": settings.environment
    }


@router.get("/health/readiness")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness check - verifies database connectivity and other dependencies.
    
    Use this endpoint to verify the service is ready to accept traffic.
    """
    checks = {}
    
    # Check database
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        checks["database"] = "error"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )
    
    # Check Redis (if configured)
    if redis_client:
        try:
            redis_client.ping()
            checks["redis"] = "ok"
        except Exception as e:
            logger.warning(f"Redis check failed: {e}")
            checks["redis"] = "warning"  # Redis is optional
    else:
        checks["redis"] = "not_configured"
    
    # Check connection pool (if available)
    try:
        pool_status = get_pool_status()
        pool_utilization = pool_status["checked_out"] / pool_status["size"] if pool_status["size"] > 0 else 0
        if pool_utilization >= 0.9:
            checks["database_pool"] = "warning"
        else:
            checks["database_pool"] = "ok"
    except (ImportError, AttributeError, ZeroDivisionError):
        pass  # Pool status not available
    
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }


@router.get("/health/liveness")
async def liveness_check():
    """
    Liveness check - verifies the service is running.
    
    Use this endpoint for Kubernetes liveness probes.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/migrations")
async def migration_status():
    """Check database migration status."""
    try:
        from alembic.config import Config
        from alembic import script
        from alembic.runtime.migration import MigrationContext
        from backend.database import engine
        
        alembic_cfg = Config("alembic.ini")
        script_dir = script.ScriptDirectory.from_config(alembic_cfg)
        
        # Get current database revision
        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            current_rev = context.get_current_revision()
        
        # Get head revision
        head_rev = script_dir.get_current_head()
        
        is_up_to_date = current_rev == head_rev
        
        return {
            "status": "up_to_date" if is_up_to_date else "pending",
            "current_revision": current_rev,
            "head_revision": head_rev,
            "pending_migrations": not is_up_to_date
        }
    except Exception as e:
        logger.warning(f"Could not check migration status: {e}")
        return {
            "status": "unknown",
            "error": str(e)
        }


@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """
    Detailed health check with all component status.
    
    Provides comprehensive system health information for monitoring and debugging.
    """
    checks = {}
    
    # Database
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = {
            "status": "ok",
            "message": "Database connection successful"
        }
    except Exception as e:
        checks["database"] = {
            "status": "error",
            "message": str(e)
        }
    
    # Connection pool
    try:
        pool_status = get_pool_status()
        pool_size = pool_status.get("size", 0)
        checked_out = pool_status.get("checked_out", 0)
        if pool_size > 0:
            utilization = checked_out / pool_size
            checks["database_pool"] = {
                "status": "ok" if utilization < 0.9 else "warning",
                "utilization": round(utilization, 3),
                "checked_out": checked_out,
                "size": pool_size,
                "available": pool_size - checked_out
            }
        else:
            checks["database_pool"] = {"status": "unknown"}
    except Exception as e:
        checks["database_pool"] = {"status": "error", "message": str(e)}
    
    # Circuit breaker
    try:
        from backend.circuit_breaker import db_circuit_breaker
        checks["circuit_breaker"] = {
            "status": "ok" if db_circuit_breaker.state == "closed" else "warning",
            "state": db_circuit_breaker.state,
            "failure_count": db_circuit_breaker.failure_count
        }
    except Exception:
        checks["circuit_breaker"] = {"status": "unknown"}
    
    # Redis
    if redis_client:
        try:
            redis_client.ping()
            checks["redis"] = {
                "status": "ok",
                "message": "Redis connection successful"
            }
        except Exception as e:
            checks["redis"] = {
                "status": "warning",
                "message": str(e)
            }
    else:
        checks["redis"] = {"status": "not_configured"}
    
    # Cache statistics
    try:
        cache_stats = get_cache_stats()
        checks["cache"] = {
            "status": "ok",
            "backend": cache_stats.get("backend", "unknown"),
            "hit_rate": cache_stats.get("hit_rate", 0),
        }
    except Exception as e:
        checks["cache"] = {"status": "error", "message": str(e)}
    
    # Cache functionality test
    try:
        test_key = "health_check_test"
        test_value = {"test": True}
        cache_set(test_key, test_value, ttl=1)
        cached = cache_get(test_key)
        cache_delete(test_key)
        checks["cache_functionality"] = {
            "status": "ok" if cached else "warning",
            "backend": "redis" if redis_client else "memory"
        }
    except Exception as e:
        checks["cache_functionality"] = {"status": "error", "message": str(e)}
    
    # Rate limiter
    try:
        # Check if Redis is being used for rate limiting
        using_redis = hasattr(limiter, "storage") and limiter.storage is not None
        checks["rate_limiter"] = {
            "status": "ok",
            "backend": "redis" if using_redis else "memory"
        }
    except Exception:
        checks["rate_limiter"] = {"status": "unknown"}
    
    overall_status = "ok"
    if any(c.get("status") == "error" for c in checks.values() if isinstance(c, dict)):
        overall_status = "error"
    elif any(c.get("status") == "warning" for c in checks.values() if isinstance(c, dict)):
        overall_status = "warning"
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }


@router.get("/system/selfcheck")
async def system_selfcheck():
    """
    System self-check endpoint - validates architectural guardrails at runtime.
    
    Returns JSON status of all guardrails. Use this for monitoring system compliance.
    """
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "unknown",
        "checks": {},
        "violations": []
    }
    
    # Check if guardrails validation script exists
    repo_root = Path(__file__).parent.parent.parent
    guardrails_script = repo_root / "infra" / "selfcheck" / "validate_guardrails.py"
    
    if not guardrails_script.exists():
        results["status"] = "error"
        results["error"] = "Guardrails validation script not found"
        return results
    
    try:
        # Run guardrails validation (non-blocking, for observability)
        result = subprocess.run(
            ["python", str(guardrails_script), "--json"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(repo_root)
        )
        
        if result.returncode == 0:
            # Parse JSON output
            try:
                validation_results = json.loads(result.stdout)
                results["checks"] = validation_results
                results["status"] = "healthy" if validation_results.get("failed", 0) == 0 else "degraded"
                results["violations"] = validation_results.get("violations", [])
            except json.JSONDecodeError:
                results["status"] = "error"
                results["error"] = "Could not parse validation results"
        else:
            results["status"] = "error"
            results["error"] = result.stderr or "Validation script failed"
            
    except subprocess.TimeoutExpired:
        results["status"] = "error"
        results["error"] = "Validation timeout"
    except Exception as e:
        results["status"] = "error"
        results["error"] = str(e)
    
    # Add runtime checks
    runtime_checks = {}
    
    # Check config validation
    try:
        settings.validate_production()
        runtime_checks["config_validation"] = "ok"
    except Exception as e:
        runtime_checks["config_validation"] = f"error: {str(e)}"
        results["violations"].append({
            "name": "config_validation",
            "severity": "critical",
            "error": str(e)
        })
        results["status"] = "degraded"
    
    # Check database pool
    try:
        pool_status = get_pool_status()
        utilization = pool_status["checked_out"] / pool_status["size"] if pool_status["size"] > 0 else 0
        runtime_checks["database_pool"] = {
            "status": "ok" if utilization < 0.9 else "warning",
            "utilization": f"{utilization:.2%}",
            "checked_out": pool_status["checked_out"],
            "size": pool_status["size"]
        }
        if utilization >= 0.9:
            results["violations"].append({
                "name": "database_pool_high_utilization",
                "severity": "high",
                "error": f"Pool utilization at {utilization:.2%}"
            })
            results["status"] = "degraded"
    except Exception as e:
        runtime_checks["database_pool"] = f"error: {str(e)}"
    
    results["checks"]["runtime"] = runtime_checks
    
    return results


@router.get("/api/v1/monitoring/metrics")
async def get_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get system metrics including cache statistics and database pool status.
    
    Requires authentication. Returns metrics for monitoring and observability.
    """
    metrics = {
        "timestamp": datetime.utcnow().isoformat(),
        "cache": get_cache_stats(),
        "database": get_pool_status(),
    }
    
    # Add circuit breaker status
    try:
        from backend.circuit_breaker import db_circuit_breaker
        metrics["circuit_breaker"] = {
            "state": db_circuit_breaker.state,
            "failure_count": db_circuit_breaker.failure_count,
        }
    except Exception:
        pass
    
    return metrics


@router.get("/api/v1/monitoring/cache/stats")
async def get_cache_statistics(
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed cache statistics.
    
    Requires authentication. Returns cache hit rate, size, and other metrics.
    """
    return get_cache_stats()


@router.get("/api/v1/monitoring/database/pool")
async def get_database_pool_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get database connection pool status.
    
    Requires authentication. Returns pool utilization and connection metrics.
    """
    pool_status = get_pool_status()
    
    # Calculate utilization
    pool_size = pool_status.get("size", 0)
    checked_out = pool_status.get("checked_out", 0)
    utilization = checked_out / pool_size if pool_size > 0 else 0
    
    return {
        **pool_status,
        "utilization": round(utilization, 3),
        "utilization_percent": round(utilization * 100, 1),
        "available": pool_size - checked_out,
    }

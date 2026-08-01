"""Centralized configuration management."""
from pydantic_settings import BaseSettings
from typing import Optional, List
from pydantic import Field, field_validator
from pydantic.config import ConfigDict
import os
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Environment
    environment: str = Field(default="development", description="Environment: development, staging, production")
    
    # Database
    database_url: str = Field(default="sqlite:///./floyo.db", description="PostgreSQL database URL")
    database_pool_size: int = Field(default=10, description="Database connection pool size")
    database_max_overflow: int = Field(default=20, description="Database connection pool max overflow")
    database_pool_recycle: int = Field(default=3600, description="Database connection pool recycle time (seconds)")
    
    # Security
    secret_key: str = Field(default="dev-secret-key-change-in-production-0000000000000000", description="JWT secret key (must be strong in production)")
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=30, description="Access token expiration (minutes)")
    refresh_token_expire_days: int = Field(default=7, description="Refresh token expiration (days)")
    
    # API
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    
    # CORS
    cors_origins: str = Field(default="http://localhost:3000", description="Comma-separated list of allowed CORS origins")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, description="Rate limit per minute")
    rate_limit_per_hour: int = Field(default=1000, description="Rate limit per hour")
    
    # Cache
    redis_url: Optional[str] = Field(default=None, description="Redis URL (optional, falls back to in-memory)")
    
    # Monitoring
    sentry_dsn: Optional[str] = Field(default=None, description="Sentry DSN for error tracking")
    
    # Frontend
    next_public_api_url: str = Field(default="http://localhost:8000", description="Frontend API URL")
    
    # Supabase (optional)
    supabase_url: Optional[str] = Field(default=None, description="Supabase URL")
    supabase_anon_key: Optional[str] = Field(default=None, description="Supabase anonymous key")
    supabase_service_role_key: Optional[str] = Field(default=None, description="Supabase service role key")
    
    # Payment Providers (optional)
    stripe_api_key: Optional[str] = Field(default=None, description="Stripe API key")
    stripe_webhook_secret: Optional[str] = Field(default=None, description="Stripe webhook secret")
    
    # Celery (optional)
    celery_broker_url: Optional[str] = Field(default=None, description="Celery broker URL (Redis)")
    celery_result_backend: Optional[str] = Field(default=None, description="Celery result backend URL")
    
    model_config = ConfigDict(
        env_file = ".env",
        env_file_encoding = "utf-8",
        case_sensitive = False,
    )

    @field_validator("cors_origins")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in v.split(",")]

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment value."""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}")
        return v

    def validate_production(self):
        """Validate production-specific settings."""
        if self.environment != "production":
            return
        
        errors = []
        
        # SECRET_KEY validation - CRITICAL: Fail if default or weak
        default_secret_patterns = [
            "your-secret-key-change-in-production",
            "CHANGE_ME_USE_STRONG_RANDOM_SECRET_KEY",
            "change_me",
            "secret",
            "default",
            "floyo"  # Prevent using project name as secret
        ]
        if any(pattern.lower() in self.secret_key.lower() for pattern in default_secret_patterns) or len(self.secret_key) < 32:
            errors.append(
                "SECRET_KEY must be set in production to a strong, random value (minimum 32 characters). "
                "Do not use default values or weak secrets. Set the SECRET_KEY environment variable."
            )
        
        # CORS validation - CRITICAL: Fail if permissive
        if "*" in self.cors_origins:
            errors.append(
                "CORS origins cannot be '*' in production. "
                "Set CORS_ORIGINS environment variable to a comma-separated list of allowed origins."
            )
        
        # Redis validation (optional but recommended)
        if not self.redis_url:
            logger.warning(
                "REDIS_URL is not set in production. "
                "Cache and rate limiting will use in-memory storage (not recommended for production)."
            )
        
        # Raise all errors at once
        if errors:
            raise ValueError("Production configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

# Create global settings instance
settings = Settings()

# Validate production settings - CRITICAL: Fail fast in production
try:
    settings.validate_production()
except ValueError as e:
    if settings.environment == "production":
        logger.error(f"CRITICAL: Production configuration validation failed: {e}")
        raise
    # In non-production, just log warning
    logger.warning(f"Configuration validation warning: {e}")
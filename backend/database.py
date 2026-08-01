"""Database connection and session management with connection pooling and circuit breaker protection."""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool, QueuePool
from sqlalchemy.event import listen
from typing import Generator
import logging
from backend.config import settings
from backend.circuit_breaker import db_circuit_breaker
from backend.sqlite_shim import SQLiteJSONB, SQLitePGUUID

logger = logging.getLogger(__name__)

# Database URL from settings
DATABASE_URL = settings.database_url

# Import and register SQLite shims for testing
from sqlalchemy.dialects.sqlite import base as sqlite_base
# The @compiles decorators in sqlite_shim.py will handle the type compilation

# For SQLite (development/testing)
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,  # Set to True for SQL logging in development
    )
else:
    # Optimize connection pooling for PostgreSQL
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_pre_ping=True,  # Verify connections before using (reconnects if stale)
        pool_size=settings.database_pool_size,  # Number of connections to maintain
        max_overflow=settings.database_max_overflow,  # Additional connections allowed beyond pool_size
        pool_recycle=settings.database_pool_recycle,  # Recycle connections after specified seconds
        pool_timeout=30,  # Timeout for getting connection from pool
        echo=False,  # Set to True for SQL logging
        connect_args={
            "connect_timeout": 10,  # Connection timeout
            "application_name": "floyo_backend",  # Identifies connection in PostgreSQL logs
        }
    )
    
    # Add connection event listeners for monitoring
    def on_connect(dbapi_conn, connection_record):
        """Called when a connection is established."""
        logger.debug("Database connection established")
    
    def on_checkout(dbapi_conn, connection_record, connection_proxy):
        """Called when a connection is checked out from the pool."""
        logger.debug("Database connection checked out from pool")
    
    listen(engine, "connect", on_connect)
    listen(engine, "checkout", on_checkout)


def get_pool_status() -> dict:
    """
    Get connection pool status for monitoring.
    
    Returns:
        dict: Pool status including size, checked in/out connections, etc.
    """
    pool = engine.pool
    return {
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "invalid": pool.invalid(),
        "pool_size": getattr(pool, "_pool_size", None),
        "max_overflow": getattr(pool, "_max_overflow", None),
    }


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Initialize database tables.
    
    Creates all tables defined in database.models if they don't exist.
    Note: In production, use Alembic migrations instead.
    """
    from database.models import Base
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")


def get_db() -> Generator[Session, None, None]:
    """
    Get database session with circuit breaker protection.
    
    This generator function yields a database session and ensures proper cleanup.
    The circuit breaker protects against cascading failures when the database is unavailable.
    
    Yields:
        Session: SQLAlchemy database session
        
    Raises:
        Exception: If circuit breaker is open or database connection fails
        
    Usage:
        ```python
        db = next(get_db())
        try:
            # Use db session
            pass
        finally:
            db.close()
        ```
        
        Or with FastAPI dependency:
        ```python
        def my_endpoint(db: Session = Depends(get_db)):
            # Use db session
            pass
        ```
    """
    # Check circuit breaker state before creating session
    if db_circuit_breaker.state == "open":
        # Check if timeout has passed
        import time
        if db_circuit_breaker.last_failure_time and \
           time.time() - db_circuit_breaker.last_failure_time > db_circuit_breaker.timeout:
            db_circuit_breaker.state = "half_open"
            logger.info("Circuit breaker transitioning to half_open for database")
        else:
            logger.warning("Circuit breaker is open for database - request rejected")
            raise Exception("Circuit breaker is open - database service unavailable")
    
    # Try to create session
    db = None
    try:
        db = SessionLocal()
        
        # Test connection with a simple query
        db.execute(text("SELECT 1"))
        
        # Success - reset circuit breaker if in half_open
        if db_circuit_breaker.state == "half_open":
            db_circuit_breaker.state = "closed"
            db_circuit_breaker.failure_count = 0
            logger.info("Circuit breaker closed for database after successful request")
        
        yield db
    except Exception as e:
        # Failure - increment failure count
        import time
        db_circuit_breaker.failure_count += 1
        db_circuit_breaker.last_failure_time = time.time()
        
        if db_circuit_breaker.failure_count >= db_circuit_breaker.failure_threshold:
            db_circuit_breaker.state = "open"
            logger.error(
                f"Circuit breaker opened for database "
                f"after {db_circuit_breaker.failure_count} failures: {e}"
            )
        
        # Close session if it was created
        if db is not None:
            db.close()
        
        raise
    finally:
        # Always close session
        if db is not None:
            db.close()

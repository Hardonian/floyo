"""
Pytest configuration for Floyo backend tests.
Sets up test database URL BEFORE importing app modules.
"""
import os
import sys
from pathlib import Path

# Set test database URL BEFORE any backend modules are imported
# This must happen before backend.database or backend.config is imported
os.environ["DATABASE_URL"] = "sqlite:///./test_floyo.db"

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Now import after DATABASE_URL is set
from backend.database import engine, SessionLocal
from database.models import Base, User, Event, Pattern, Suggestion, Workflow, Organization

# Override engine for testing
test_engine = create_engine(
    "sqlite:///./test_floyo.db",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create test database tables before all tests."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    # Clean up test database file
    import os
    if os.path.exists("./test_floyo.db"):
        os.remove("./test_floyo.db")


@pytest.fixture
def db_session():
    """Create a fresh database session for each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def mock_user():
    """Create a mock user for tests."""
    from uuid import uuid4
    user = User(
        id=uuid4(),
        email="test@example.com",
        username="testuser",
        hashed_password="hashed",
        is_active=True,
        is_superuser=False,
    )
    return user
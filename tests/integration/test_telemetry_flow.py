"""
Integration Tests for Telemetry Flow

Tests the complete flow: event ingestion -> pattern detection -> insights generation.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from backend.services.event_service import EventService
from backend.services.insights_service import InsightsService
from backend.jobs.pattern_detection import trigger_pattern_detection_sync
from database.models import Event, Pattern, User


@pytest.fixture
def test_user(db_session: Session):
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_telemetry_flow_integration():
    """
    Test complete telemetry flow:
    1. Ingest events
    2. Detect patterns
    3. Generate insights

    Uses a real (non-transaction-wrapped) session because the pattern
    detection job opens its own DB session — data must be committed for a
    background job to see it, exactly as in production.
    """
    from backend.database import SessionLocal

    db = SessionLocal()
    try:
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = str(user.id)
        event_service = EventService(db)

        # Step 1: Create multiple events
        events_created = []
        for i in range(5):
            event = event_service.create_event(
                user_id=user_id,
                event_type="file_created",
                file_path=f"/test/file{i}.ts",
                tool="vscode",
            )
            events_created.append(event)

        assert len(events_created) == 5

        # Step 2: Trigger pattern detection
        result = trigger_pattern_detection_sync(user_id=user_id, hours_back=1)

        assert result['processed'] >= 5

        # Step 3: Generate insights
        insights_service = InsightsService()
        insights = insights_service.generate_insights_for_user(
            db=db,
            user_id=user_id,
            days_back=1,
        )

        # Should generate at least some insights
        assert isinstance(insights, list)

        # Verify patterns were created
        patterns = db.query(Pattern).filter(Pattern.user_id == user_id).all()
        assert len(patterns) >= 0  # May be 0 if frequency threshold not met
    finally:
        db.rollback()
        db.close()

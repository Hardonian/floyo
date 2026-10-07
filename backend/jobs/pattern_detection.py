"""
Pattern Detection Background Job

Processes telemetry events and detects patterns within 1 hour of ingestion.
Runs periodically or can be triggered manually.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from celery import shared_task

from backend.database import SessionLocal
from backend.logging_config import get_logger
from backend.ml.pattern_detector import AdvancedPatternDetector
from database.models import Event, Pattern, User

logger = get_logger(__name__)


@shared_task(name='pattern_detection.process_events', bind=True)
def process_events_task(self, user_id: str = None, hours_back: int = 1):
    """
    Process events and detect patterns.
    
    Args:
        user_id: Optional user ID to process events for. If None, processes all users.
        hours_back: Number of hours to look back for events (default: 1 hour)
    
    Returns:
        Dict with processing results
    """
    db = SessionLocal()
    try:
        detector = AdvancedPatternDetector()
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        # Get events to process
        query = db.query(Event).filter(Event.timestamp >= cutoff_time)
        if user_id:
            query = query.filter(Event.user_id == user_id)
        
        events = query.order_by(Event.timestamp).all()
        
        if not events:
            logger.info(f"No events found in the last {hours_back} hour(s)")
            return {
                'processed': 0,
                'patterns_created': 0,
                'patterns_updated': 0,
            }
        
        # Group events by user
        events_by_user: Dict[str, List[Event]] = {}
        for event in events:
            if event.user_id not in events_by_user:
                events_by_user[event.user_id] = []
            events_by_user[event.user_id].append(event)
        
        total_processed = 0
        patterns_created = 0
        patterns_updated = 0
        
        # Process each user's events
        for user_id, user_events in events_by_user.items():
            try:
                # Convert events to dict format for pattern detector
                event_dicts = [
                    {
                        'filePath': event.file_path,
                        'eventType': event.event_type,
                        'tool': event.tool or 'unknown',
                        'timestamp': event.timestamp.isoformat(),
                        'metadata': event.details or {},
                    }
                    for event in user_events
                ]
                
                # Detect patterns
                patterns = detector.detect_repetitive_patterns(
                    sequences=[event_dicts],
                    min_frequency=3
                )
                
                # Batch load existing patterns to avoid N+1 queries
                file_extensions = [
                    _extract_file_extension(p) for p in patterns
                    if _extract_file_extension(p)
                ]
                
                existing_patterns = {
                    p.file_extension: p
                    for p in db.query(Pattern).filter(
                        Pattern.user_id == user_id,
                        Pattern.file_extension.in_(file_extensions)
                    ).all()
                }
                
                # Update or create Pattern records
                for pattern_data in patterns:
                    file_extension = _extract_file_extension(pattern_data)
                    if not file_extension:
                        continue
                    
                    # Get existing pattern from batch-loaded dict
                    pattern = existing_patterns.get(file_extension)
                    
                    if pattern:
                        # Update existing pattern
                        pattern.count += pattern_data.get('frequency', 0)
                        pattern.last_used = datetime.utcnow()
                        if 'tools' in pattern_data:
                            existing_tools = set(pattern.tools or [])
                            new_tools = set(pattern_data.get('tools', []))
                            pattern.tools = list(existing_tools | new_tools)
                        patterns_updated += 1
                    else:
                        # Create new pattern
                        pattern = Pattern(
                            user_id=user_id,
                            file_extension=file_extension,
                            count=pattern_data.get('frequency', 0),
                            last_used=datetime.utcnow(),
                            tools=pattern_data.get('tools', []),
                        )
                        db.add(pattern)
                        patterns_created += 1
                        # Add to dict to avoid duplicates
                        existing_patterns[file_extension] = pattern
                
                total_processed += len(user_events)
                
            except Exception as e:
                logger.error(f"Error processing events for user {user_id}: {e}", exc_info=True)
                continue
        
        db.commit()
        
        logger.info(
            f"Pattern detection completed: {total_processed} events processed, "
            f"{patterns_created} patterns created, {patterns_updated} patterns updated"
        )
        
        return {
            'processed': total_processed,
            'patterns_created': patterns_created,
            'patterns_updated': patterns_updated,
            'users_processed': len(events_by_user),
        }
        
    except Exception as e:
        logger.error(f"Pattern detection task failed: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


def _extract_file_extension(pattern_data: Dict[str, Any]) -> str:
    """Extract file extension from pattern data."""
    # Try to get file extension from sequences
    sequences = pattern_data.get('sequences', [])
    if sequences and len(sequences) > 0:
        first_sequence = sequences[0]
        if first_sequence and len(first_sequence) > 0:
            file_path = first_sequence[0].get('filePath', '')
            if '.' in file_path:
                return '.' + file_path.split('.')[-1]
    
    # Fallback: try to get from sequence_key
    sequence_key = pattern_data.get('sequence_key', '')
    if '.' in sequence_key:
        return '.' + sequence_key.split('.')[-1]
    
    return ''


@shared_task(name='pattern_detection.process_user_patterns', bind=True)
def process_user_patterns_task(self, user_id: str):
    """
    Process patterns for a specific user.
    
    Args:
        user_id: User ID to process patterns for
    
    Returns:
        Dict with processing results
    """
    return process_events_task(user_id=user_id, hours_back=24)


# Manual trigger function for testing (synchronous)
def trigger_pattern_detection_sync(user_id: str = None, hours_back: int = 1):
    """
    Manually trigger pattern detection synchronously (for testing).
    
    Args:
        user_id: Optional user ID to process
        hours_back: Hours to look back
    
    Returns:
        Processing results
    """
    return process_events_task(user_id=user_id, hours_back=hours_back)


# Async trigger function (for Celery)
def trigger_pattern_detection(user_id: str = None, hours_back: int = 1):
    """
    Manually trigger pattern detection asynchronously (for production).
    
    Args:
        user_id: Optional user ID to process
        hours_back: Hours to look back
    
    Returns:
        Celery task result
    """
    return process_events_task.delay(user_id=user_id, hours_back=hours_back)

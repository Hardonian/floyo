"""API endpoints for insights and recommendations."""

import sys
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.database import get_db
from backend.logging_config import get_logger
from backend.auth.utils import get_current_user
from backend.cache import cached
from database.models import User, Pattern, Event
from backend.services.insights_service import InsightsService

logger = get_logger(__name__)
router = APIRouter(prefix="/api/insights", tags=["insights"])


@router.get("")
@cached(ttl_seconds=300, key_prefix="insights")
async def get_insights(
    days_back: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get insights and recommendations for the current user.
    
    Returns:
        List of insights with recommendations
    """
    try:
        service = InsightsService()
        insights = service.generate_insights_for_user(
            db,
            str(current_user.id),
            days_back
        )
        
        recommendations = service.generate_recommendations_from_insights(insights)
        
        return {
            "insights": insights,
            "recommendations": recommendations,
            "count": len(insights),
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting insights: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate insights: {str(e)}"
        )


@router.get("/patterns")
@cached(ttl_seconds=300, key_prefix="patterns")
async def get_patterns(
    days_back: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detected patterns for the current user.
    
    Returns:
        List of patterns with metadata
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        patterns = db.query(Pattern).filter(
            Pattern.user_id == str(current_user.id)
        ).all()
        
        # Batch load event counts to avoid N+1 queries
        # Get all file extensions from patterns
        file_extensions = [p.file_extension for p in patterns]
        
        # Batch query event counts grouped by file extension
        from sqlalchemy import func
        event_counts_query = db.query(
            Event.file_path,
            func.count(Event.id).label('count')
        ).filter(
            Event.user_id == str(current_user.id),
            Event.created_at >= cutoff_date
        ).group_by(Event.file_path).all()
        
        # Build a map of file extension to event count
        extension_event_map = {}
        for file_path, count in event_counts_query:
            # Extract extension from file path
            if '.' in file_path:
                ext = file_path.split('.')[-1].lower()
                extension_event_map[ext] = extension_event_map.get(ext, 0) + count
        
        # Build pattern data with batch-loaded event counts
        pattern_data = []
        for pattern in patterns:
            event_count = extension_event_map.get(pattern.file_extension.lower(), 0)
            
            pattern_data.append({
                "id": str(pattern.id),
                "file_extension": pattern.file_extension,
                "count": pattern.count,
                "event_count": event_count,
                "last_used": pattern.last_used.isoformat() if pattern.last_used else None,
                "tools": pattern.tools or [],
            })
        
        return {
            "patterns": pattern_data,
            "count": len(pattern_data),
            "period_days": days_back
        }
    except Exception as e:
        logger.error(f"Error getting patterns: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get patterns: {str(e)}"
        )


@router.get("/stats")
@cached(ttl_seconds=300, key_prefix="stats")
async def get_stats(
    days_back: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get statistics for the current user.
    
    Returns:
        User statistics including event counts, patterns, etc.
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Count events
        event_count = db.query(Event).filter(
            Event.user_id == str(current_user.id),
            Event.created_at >= cutoff_date
        ).count()
        
        # Count patterns
        pattern_count = db.query(Pattern).filter(
            Pattern.user_id == str(current_user.id)
        ).count()
        
        # Get unique tools used
        tools_query = db.query(Event.tool).filter(
            Event.user_id == str(current_user.id),
            Event.created_at >= cutoff_date,
            Event.tool.isnot(None)
        ).distinct().all()
        unique_tools = [tool[0] for tool in tools_query if tool[0]]
        
        # Get unique file extensions
        extensions_query = db.query(Pattern.file_extension).filter(
            Pattern.user_id == str(current_user.id)
        ).distinct().all()
        unique_extensions = [ext[0] for ext in extensions_query if ext[0]]
        
        return {
            "event_count": event_count,
            "pattern_count": pattern_count,
            "unique_tools": len(unique_tools),
            "unique_extensions": len(unique_extensions),
            "tools": unique_tools,
            "extensions": unique_extensions,
            "period_days": days_back,
            "period_start": cutoff_date.isoformat(),
            "period_end": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )

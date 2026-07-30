"""
Activity Tracker Repository for Rafeeq Enterprise Islamic OS.
Logs every piece of content consumed by the user for "No-Repeat" experience.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Float, ForeignKey, JSON, select, and_, or_, desc, func
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text

from models.base import Base
from models.knowledge_graph import ContentNode, ContentTheme, Theme
from .base import BaseRepository

logger = logging.getLogger(__name__)


class UserActivityLog(Base):
    """User activity log for tracking content consumption"""
    __tablename__ = "user_activity_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    content_node_id = Column(Integer, ForeignKey("content_nodes.id"), nullable=False, index=True)
    
    # Activity metadata
    content_type = Column(String(50), nullable=False, index=True)
    source_id = Column(String(100), nullable=False, index=True)
    view_duration_seconds = Column(Integer, nullable=True)  # How long user viewed content
    completion_percentage = Column(Float, default=0.0)  # 0.0 to 1.0
    
    # Context
    session_id = Column(String(100), nullable=True)  # For grouping related activities
    context = Column(JSON, nullable=True)  # Additional context data
    
    # Timestamps
    viewed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    content_node = relationship("ContentNode")
    
    def __repr__(self):
        return f"<UserActivityLog(user_id={self.user_id}, content={self.content_node_id})>"


class ActivityTrackerRepository(BaseRepository[UserActivityLog]):
    """
    Repository for tracking user content consumption.
    Implements "No-Repeat" logic by excluding seen content.
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(UserActivityLog, session)
    
    async def log_activity(
        self,
        user_id: int,
        content_node_id: int,
        content_type: str,
        source_id: str,
        view_duration_seconds: Optional[int] = None,
        completion_percentage: float = 0.0,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> UserActivityLog:
        """
        Log user content consumption activity.
        
        Args:
            user_id: User ID
            content_node_id: Content node ID
            content_type: Type of content
            source_id: Source identifier
            view_duration_seconds: Duration of view in seconds
            completion_percentage: Completion percentage (0.0 to 1.0)
            session_id: Session identifier for grouping
            context: Additional context data
        
        Returns:
            Created activity log
        """
        activity = UserActivityLog(
            user_id=user_id,
            content_node_id=content_node_id,
            content_type=content_type,
            source_id=source_id,
            view_duration_seconds=view_duration_seconds,
            completion_percentage=completion_percentage,
            session_id=session_id,
            context=context
        )
        return await self.create(activity)
    
    async def get_seen_content_ids(
        self,
        user_id: int,
        content_type: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[int]:
        """
        Get list of content node IDs seen by user.
        
        Args:
            user_id: User ID
            content_type: Filter by content type (optional)
            since: Only get content seen since this date (optional)
        
        Returns:
            List of content node IDs
        """
        try:
            query = select(UserActivityLog.content_node_id).where(
                UserActivityLog.user_id == user_id
            )
            
            if content_type:
                query = query.where(UserActivityLog.content_type == content_type)
            
            if since:
                query = query.where(UserActivityLog.viewed_at >= since)
            
            result = await self.session.execute(query)
            return [row[0] for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Error getting seen content for user {user_id}: {e}")
            return []
    
    async def get_unseen_content(
        self,
        user_id: int,
        content_type: Optional[str] = None,
        limit: int = 10
    ) -> List[ContentNode]:
        """
        Get content that user hasn't seen yet.
        
        Args:
            user_id: User ID
            content_type: Filter by content type (optional)
            limit: Maximum number of results
        
        Returns:
            List of unseen content nodes
        """
        try:
            # Get seen content IDs
            seen_ids = await self.get_seen_content_ids(user_id, content_type)
            
            # Build query for unseen content
            query = select(ContentNode).where(
                ContentNode.id.notin_(seen_ids) if seen_ids else True
            )
            
            if content_type:
                query = query.where(ContentNode.content_type == content_type)
            
            query = query.order_by(func.random()).limit(limit)
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting unseen content for user {user_id}: {e}")
            return []
    
    async def get_random_unseen_content(
        self,
        user_id: int,
        content_type: Optional[str] = None,
        limit: int = 1
    ) -> Optional[ContentNode]:
        """
        Get random unseen content for user.
        
        Args:
            user_id: User ID
            content_type: Filter by content type (optional)
            limit: Number of results (default 1)
        
        Returns:
            Random unseen content node or None
        """
        unseen_content = await self.get_unseen_content(user_id, content_type, limit)
        return unseen_content[0] if unseen_content else None
    
    async def get_user_activity_stats(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get user activity statistics.
        
        Args:
            user_id: User ID
            start_date: Start date for analysis
            end_date: End date for analysis
        
        Returns:
            Dictionary with activity statistics
        """
        try:
            if start_date is None:
                start_date = datetime.now(timezone.utc) - timedelta(days=30)
            if end_date is None:
                end_date = datetime.now(timezone.utc)
            
            # Total activities
            total_result = await self.session.execute(
                select(func.count(UserActivityLog.id))
                .where(
                    and_(
                        UserActivityLog.user_id == user_id,
                        UserActivityLog.viewed_at >= start_date,
                        UserActivityLog.viewed_at <= end_date
                    )
                )
            )
            total_activities = total_result.scalar() or 0
            
            # Activities by type
            by_type_result = await self.session.execute(
                select(
                    UserActivityLog.content_type,
                    func.count(UserActivityLog.id).label('count')
                )
                .where(
                    and_(
                        UserActivityLog.user_id == user_id,
                        UserActivityLog.viewed_at >= start_date,
                        UserActivityLog.viewed_at <= end_date
                    )
                )
                .group_by(UserActivityLog.content_type)
            )
            
            by_type = {row.content_type: row.count for row in by_type_result}
            
            # Average completion rate
            completion_result = await self.session.execute(
                select(func.avg(UserActivityLog.completion_percentage))
                .where(
                    and_(
                        UserActivityLog.user_id == user_id,
                        UserActivityLog.viewed_at >= start_date,
                        UserActivityLog.viewed_at <= end_date
                    )
                )
            )
            avg_completion = completion_result.scalar() or 0.0
            
            return {
                "user_id": user_id,
                "total_activities": total_activities,
                "activities_by_type": by_type,
                "average_completion_rate": round(avg_completion * 100, 2),
                "period_days": (end_date - start_date).days
            }
        except Exception as e:
            logger.error(f"Error getting activity stats for user {user_id}: {e}")
            return {}
    
    async def get_content_consumers(
        self,
        content_node_id: int,
        limit: int = 100
    ) -> List[int]:
        """
        Get list of user IDs who have consumed specific content.
        
        Args:
            content_node_id: Content node ID
            limit: Maximum number of users
        
        Returns:
            List of user IDs
        """
        try:
            result = await self.session.execute(
                select(UserActivityLog.user_id)
                .where(UserActivityLog.content_node_id == content_node_id)
                .distinct()
                .limit(limit)
            )
            return [row[0] for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Error getting consumers for content {content_node_id}: {e}")
            return []
    
    async def clear_old_activities(
        self,
        older_than_days: int = 90,
        user_id: Optional[int] = None
    ) -> int:
        """
        Clear old activity logs.
        
        Args:
            older_than_days: Age threshold in days
            user_id: Specific user ID (optional, clears all if None)
        
        Returns:
            Number of activities cleared
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=older_than_days)
            
            query = select(UserActivityLog).where(
                UserActivityLog.viewed_at < cutoff_date
            )
            
            if user_id:
                query = query.where(UserActivityLog.user_id == user_id)
            
            result = await self.session.execute(query)
            activities = result.scalars().all()
            
            count = 0
            for activity in activities:
                await self.delete(activity)
                count += 1
            
            logger.info(f"Cleared {count} old activities")
            return count
        except Exception as e:
            logger.error(f"Error clearing old activities: {e}")
            return 0
    
    async def get_reading_session(
        self,
        session_id: str
    ) -> List[UserActivityLog]:
        """
        Get all activities in a specific reading session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            List of activities in the session
        """
        try:
            result = await self.session.execute(
                select(UserActivityLog)
                .where(UserActivityLog.session_id == session_id)
                .order_by(UserActivityLog.viewed_at)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return []
    
    async def get_user_themes(
        self,
        user_id: int,
        limit: int = 10
    ) -> List[Theme]:
        """
        Get themes that user has engaged with most.
        
        Args:
            user_id: User ID
            limit: Maximum number of themes
        
        Returns:
            List of themes with engagement count
        """
        try:
            result = await self.session.execute(
                select(
                    Theme,
                    func.count(ContentTheme.content_node_id).label('engagement_count')
                )
                .join(ContentTheme, Theme.id == ContentTheme.theme_id)
                .join(UserActivityLog, ContentTheme.content_node_id == UserActivityLog.content_node_id)
                .where(UserActivityLog.user_id == user_id)
                .group_by(Theme.id)
                .order_by(desc('engagement_count'))
                .limit(limit)
            )
            
            themes = []
            for row in result:
                themes.append({
                    "theme": row[0],
                    "engagement_count": row[1]
                })
            
            return themes
        except Exception as e:
            logger.error(f"Error getting user themes for user {user_id}: {e}")
            return []

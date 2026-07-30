"""
Analytics Repository for Rafeeq Enterprise Islamic OS.
Tracks DAU, plugin usage, errors, and system health metrics.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.sql import text

from models.metrics import UserMetrics, ModuleUsage
from .base import BaseRepository

logger = logging.getLogger(__name__)


class AnalyticsRepository(BaseRepository[UserMetrics]):
    """
    Repository for analytics and metrics operations.
    Provides DAU tracking, plugin usage analysis, and error monitoring.
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(UserMetrics, session)
    
    async def get_dau(self, date: Optional[datetime] = None) -> int:
        """
        Get Daily Active Users (DAU) for a specific date.
        
        Args:
            date: Date to check (defaults to today)
        
        Returns:
            Number of active users
        """
        if date is None:
            date = datetime.now(timezone.utc).date()
        
        try:
            # Query users who were active on the specified date
            start_of_day = datetime.combine(date, datetime.min.time()).replace(tzinfo=timezone.utc)
            end_of_day = datetime.combine(date, datetime.max.time()).replace(tzinfo=timezone.utc)
            
            from models.user import User
            result = await self.session.execute(
                select(func.count(User.id))
                .where(
                    and_(
                        User.last_active_date >= start_of_day,
                        User.last_active_date <= end_of_day
                    )
                )
            )
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error getting DAU for {date}: {e}")
            return 0
    
    async def get_mau(self, year: int, month: int) -> int:
        """
        Get Monthly Active Users (MAU) for a specific month.
        
        Args:
            year: Year
            month: Month (1-12)
        
        Returns:
            Number of active users
        """
        try:
            start_of_month = datetime(year, month, 1).replace(tzinfo=timezone.utc)
            if month == 12:
                end_of_month = datetime(year + 1, 1, 1).replace(tzinfo=timezone.utc)
            else:
                end_of_month = datetime(year, month + 1, 1).replace(tzinfo=timezone.utc)
            
            from models.user import User
            result = await self.session.execute(
                select(func.count(User.id))
                .where(
                    and_(
                        User.last_active_date >= start_of_month,
                        User.last_active_date < end_of_month
                    )
                )
            )
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error getting MAU for {year}-{month}: {e}")
            return 0
    
    async def get_plugin_usage_stats(
        self,
        module_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get usage statistics for a specific plugin/module.
        
        Args:
            module_name: Name of the module
            start_date: Start date for analysis
            end_date: End date for analysis
        
        Returns:
            Dictionary with usage statistics
        """
        try:
            if start_date is None:
                start_date = datetime.now(timezone.utc) - timedelta(days=30)
            if end_date is None:
                end_date = datetime.now(timezone.utc)
            
            # Total uses
            total_uses_result = await self.session.execute(
                select(func.count(ModuleUsage.id))
                .where(
                    and_(
                        ModuleUsage.module_name == module_name,
                        ModuleUsage.timestamp >= start_date,
                        ModuleUsage.timestamp <= end_date
                    )
                )
            )
            total_uses = total_uses_result.scalar() or 0
            
            # Unique users
            unique_users_result = await self.session.execute(
                select(func.count(func.distinct(ModuleUsage.user_id)))
                .where(
                    and_(
                        ModuleUsage.module_name == module_name,
                        ModuleUsage.timestamp >= start_date,
                        ModuleUsage.timestamp <= end_date
                    )
                )
            )
            unique_users = unique_users_result.scalar() or 0
            
            # Average daily uses
            days = (end_date - start_date).days or 1
            avg_daily_uses = total_uses / days
            
            return {
                "module_name": module_name,
                "total_uses": total_uses,
                "unique_users": unique_users,
                "avg_daily_uses": round(avg_daily_uses, 2),
                "period_days": days
            }
        except Exception as e:
            logger.error(f"Error getting plugin usage stats for {module_name}: {e}")
            return {}
    
    async def get_all_plugin_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get usage statistics for all plugins.
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
        
        Returns:
            List of plugin statistics
        """
        try:
            if start_date is None:
                start_date = datetime.now(timezone.utc) - timedelta(days=30)
            if end_date is None:
                end_date = datetime.now(timezone.utc)
            
            result = await self.session.execute(
                select(
                    ModuleUsage.module_name,
                    func.count(ModuleUsage.id).label('total_uses'),
                    func.count(func.distinct(ModuleUsage.user_id)).label('unique_users')
                )
                .where(
                    and_(
                        ModuleUsage.timestamp >= start_date,
                        ModuleUsage.timestamp <= end_date
                    )
                )
                .group_by(ModuleUsage.module_name)
                .order_by(desc('total_uses'))
            )
            
            stats = []
            for row in result:
                stats.append({
                    "module_name": row.module_name,
                    "total_uses": row.total_uses,
                    "unique_users": row.unique_users
                })
            
            return stats
        except Exception as e:
            logger.error(f"Error getting all plugin stats: {e}")
            return []
    
    async def get_user_engagement_metrics(self, user_id: int) -> Dict[str, Any]:
        """
        Get engagement metrics for a specific user.
        
        Args:
            user_id: User ID
        
        Returns:
            Dictionary with engagement metrics
        """
        try:
            # Get user metrics
            metrics = await self.get_by_id(user_id)
            if not metrics:
                return {}
            
            # Get module usage breakdown
            usage_result = await self.session.execute(
                select(
                    ModuleUsage.module_name,
                    func.count(ModuleUsage.id).label('count')
                )
                .where(ModuleUsage.user_id == user_id)
                .group_by(ModuleUsage.module_name)
                .order_by(desc('count'))
            )
            
            module_usage = {row.module_name: row.count for row in usage_result}
            
            # Calculate engagement score
            total_actions = metrics.total_messages + metrics.quran_ayahs_read + metrics.prayers_completed
            engagement_score = min(100, (total_actions / 100) * 100)  # Normalize to 0-100
            
            return {
                "user_id": user_id,
                "total_messages": metrics.total_messages,
                "quran_ayahs_read": metrics.quran_ayahs_read,
                "prayers_completed": metrics.prayers_completed,
                "adhkar_completed": metrics.adhkar_completed,
                "xp_points": metrics.xp_points,
                "level": metrics.level,
                "module_usage": module_usage,
                "engagement_score": round(engagement_score, 2)
            }
        except Exception as e:
            logger.error(f"Error getting engagement metrics for user {user_id}: {e}")
            return {}
    
    async def get_top_users_by_xp(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top users by XP points.
        
        Args:
            limit: Number of users to return
        
        Returns:
            List of user XP rankings
        """
        try:
            result = await self.session.execute(
                select(UserMetrics)
                .order_by(desc(UserMetrics.xp_points))
                .limit(limit)
            )
            
            rankings = []
            for rank, metrics in enumerate(result, 1):
                rankings.append({
                    "rank": rank,
                    "user_id": metrics.id,
                    "xp_points": metrics.xp_points,
                    "level": metrics.level
                })
            
            return rankings
        except Exception as e:
            logger.error(f"Error getting top users по XP: {e}")
            return []
    
    async def get_error_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get error statistics from logs.
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
        
        Returns:
            Dictionary with error statistics
        """
        try:
            if start_date is None:
                start_date = datetime.now(timezone.utc) - timedelta(days=7)
            if end_date is None:
                end_date = datetime.now(timezone.utc)
            
            # This would typically query a separate error log table
            # For now, return placeholder data
            return {
                "total_errors": 0,
                "critical_errors": 0,
                "warning_errors": 0,
                "period_days": (end_date - start_date).days
            }
        except Exception as e:
            logger.error(f"Error getting error stats: {e}")
            return {}
    
    async def get_system_health_summary(self) -> Dict[str, Any]:
        """
        Get overall system health summary.
        
        Returns:
            Dictionary with health metrics
        """
        try:
            # Get current DAU
            today_dau = await self.get_dau()
            
            # Get yesterday's DAU for comparison
            yesterday = datetime.now(timezone.utc) - timedelta(days=1)
            yesterday_dau = await self.get_dau(yesterday.date())
            
            # Calculate growth
            dau_growth = 0
            if yesterday_dau > 0:
                dau_growth = round(((today_dau - yesterday_dau) / yesterday_dau) * 100, 2)
            
            # Get total users
            from models.user import User
            total_users_result = await self.session.execute(
                select(func.count(User.id))
            )
            total_users = total_users_result.scalar() or 0
            
            # Get plugin stats
            plugin_stats = await self.get_all_plugin_stats()
            
            return {
                "dau": today_dau,
                "dau_growth_percent": dau_growth,
                "total_users": total_users,
                "active_plugins": len(plugin_stats),
                "plugin_stats": plugin_stats[:5],  # Top 5 plugins
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting system health summary: {e}")
            return {}
    
    async def get_retention_metrics(
        self,
        cohort_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get user retention metrics for a cohort.
        
        Args:
            cohort_date: Date of user cohort (defaults to 7 days ago)
        
        Returns:
            Dictionary with retention metrics
        """
        try:
            if cohort_date is None:
                cohort_date = datetime.now(timezone.utc) - timedelta(days=7)
            
            from models.user import User
            
            # Get users who joined on cohort date
            start_of_day = datetime.combine(cohort_date.date(), datetime.min.time()).replace(tzinfo=timezone.utc)
            end_of_day = datetime.combine(cohort_date.date(), datetime.max.time()).replace(tzinfo=timezone.utc)
            
            cohort_users_result = await self.session.execute(
                select(func.count(User.id))
                .where(
                    and_(
                        User.created_at >= start_of_day,
                        User.created_at <= end_of_day
                    )
                )
            )
            cohort_size = cohort_users_result.scalar() or 0
            
            if cohort_size == 0:
                return {"cohort_size": 0, "retention_rates": {}}
            
            # Calculate retention for different time periods
            retention_rates = {}
            for days in [1, 3, 7, 14, 30]:
                retention_date = cohort_date + timedelta(days=days)
                if retention_date > datetime.now(timezone.utc):
                    continue
                
                start_retention = datetime.combine(retention_date.date(), datetime.min.time()).replace(tzinfo=timezone.utc)
                end_retention = datetime.combine(retention_date.date(), datetime.max.time()).replace(tzinfo=timezone.utc)
                
                retained_result = await self.session.execute(
                    select(func.count(User.id))
                    .where(
                        and_(
                            User.created_at >= start_of_day,
                            User.created_at <= end_of_day,
                            User.last_active_date >= start_retention,
                            User.last_active_date <= end_retention
                        )
                    )
                )
                retained_count = retained_result.scalar() or 0
                
                retention_rate = round((retained_count / cohort_size) * 100, 2)
                retention_rates[f"day_{days}"] = retention_rate
            
            return {
                "cohort_date": cohort_date.date().isoformat(),
                "cohort_size": cohort_size,
                "retention_rates": retention_rates
            }
        except Exception as e:
            logger.error(f"Error getting retention metrics: {e}")
            return {}

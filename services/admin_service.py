"""
Admin Service for Rafeeq Bot Command Center
Provides advanced analytics, user management, broadcast, and system control features.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.dialects.postgresql import insert

from models.user import User, Role
from models.metrics import UserMetrics, ModuleUsage
from repositories.activity_tracker import ActivityTrackerRepository
from utils.redis_client import redis_client

logger = logging.getLogger(__name__)


class AdminService:
    """Service for admin operations and analytics"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.redis = redis_client
        self.activity_tracker = ActivityTrackerRepository(db)
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health metrics"""
        try:
            # Database health
            db_result = await self.db.execute(select(func.count(User.id)))
            total_users = db_result.scalar() or 0
            
            # Active users (last 24 hours)
            active_24h = await self.db.execute(
                select(func.count(User.id)).where(
                    User.last_active_date >= datetime.now() - timedelta(hours=24)
                )
            )
            active_24h = active_24h.scalar() or 0
            
            # Active users (last 7 days)
            active_7d = await self.db.execute(
                select(func.count(User.id)).where(
                    User.last_active_date >= datetime.now() - timedelta(days=7)
                )
            )
            active_7d = active_7d.scalar() or 0
            
            # Active users (last 30 days)
            active_30d = await self.db.execute(
                select(func.count(User.id)).where(
                    User.last_active_date >= datetime.now() - timedelta(days=30)
                )
            )
            active_30d = active_30d.scalar() or 0
            
            # Redis health
            redis_info = {}
            if self.redis and self.redis.client:
                try:
                    redis_info = await self.redis.client.info()
                    redis_memory = redis_info.get('used_memory_human', 'N/A')
                    redis_connected_clients = redis_info.get('connected_clients', 0)
                except Exception as e:
                    logger.error(f"Error getting Redis info: {e}")
                    redis_memory = 'Error'
                    redis_connected_clients = 0
            else:
                redis_memory = 'Not connected'
                redis_connected_clients = 0
            
            return {
                'total_users': total_users,
                'active_24h': active_24h,
                'active_7d': active_7d,
                'active_30d': active_30d,
                'dau': active_24h,
                'mau': active_30d,
                'redis_memory': redis_memory,
                'redis_clients': redis_connected_clients,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {}
    
    async def get_module_usage_stats(self) -> Dict[str, Any]:
        """Get module usage statistics"""
        try:
            # Get module usage from last 7 days
            seven_days_ago = datetime.now() - timedelta(days=7)
            
            result = await self.db.execute(
                select(
                    ModuleUsage.module_name,
                    func.count(ModuleUsage.id).label('usage_count')
                ).where(
                    ModuleUsage.timestamp >= seven_days_ago
                ).group_by(ModuleUsage.module_name)
            )
            
            module_stats = {}
            for row in result:
                module_stats[row.module_name] = row.usage_count
            
            return module_stats
        except Exception as e:
            logger.error(f"Error getting module usage stats: {e}")
            return {}
    
    async def search_user(self, identifier: str) -> Optional[User]:
        """Search user by ID or username"""
        try:
            # Try to parse as integer (Telegram ID)
            try:
                user_id = int(identifier)
                result = await self.db.execute(select(User).where(User.id == user_id))
                return result.scalar_one_or_none()
            except ValueError:
                pass
            
            # Search by username
            result = await self.db.execute(
                select(User).where(User.username.ilike(f"%{identifier}%"))
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error searching user: {e}")
            return None
    
    async def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed user profile"""
        try:
            result = await self.db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            # Get user metrics
            metrics_result = await self.db.execute(
                select(UserMetrics).where(UserMetrics.user_id == user_id)
            )
            metrics = metrics_result.scalar_one_or_none()
            
            # Get recent activity
            recent_activity = await self.activity_tracker.get_user_activity_stats(user_id)
            
            return {
                'user': user,
                'metrics': metrics,
                'recent_activity': recent_activity
            }
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None
    
    async def ban_user(self, user_id: int, reason: str = "") -> bool:
        """Ban a user"""
        try:
            result = await self.db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if not user:
                return False
            
            user.is_banned = True
            user.ban_reason = reason
            user.banned_at = datetime.now()
            await self.db.commit()
            
            logger.info(f"User {user_id} banned. Reason: {reason}")
            return True
        except Exception as e:
            logger.error(f"Error banning user: {e}")
            await self.db.rollback()
            return False
    
    async def unban_user(self, user_id: int) -> bool:
        """Unban a user"""
        try:
            result = await self.db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if not user:
                return False
            
            user.is_banned = False
            user.ban_reason = None
            user.banned_at = None
            await self.db.commit()
            
            logger.info(f"User {user_id} unbanned")
            return True
        except Exception as e:
            logger.error(f"Error unbanning user: {e}")
            await self.db.rollback()
            return False
    
    async def get_banned_users(self) -> List[User]:
        """Get list of banned users"""
        try:
            result = await self.db.execute(
                select(User).where(User.is_banned == True)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting banned users: {e}")
            return []
    
    async def broadcast_message(
        self, 
        message_text: str, 
        target_type: str = "all",
        parse_mode: str = None
    ) -> Dict[str, int]:
        """
        Broadcast message to users
        target_type: 'all', 'active', 'inactive'
        Returns: {'total': int, 'success': int, 'failed': int}
        """
        try:
            # Build query based on target type
            query = select(User).where(User.is_banned == False)
            
            if target_type == "active":
                query = query.where(
                    User.last_active_date >= datetime.now() - timedelta(days=7)
                )
            elif target_type == "inactive":
                query = query.where(
                    User.last_active_date < datetime.now() - timedelta(days=7)
                )
            
            result = await self.db.execute(query)
            users = result.scalars().all()
            
            return {
                'total': len(users),
                'users': users,
                'message': message_text,
                'parse_mode': parse_mode
            }
        except Exception as e:
            logger.error(f"Error preparing broadcast: {e}")
            return {'total': 0, 'users': [], 'message': message_text}
    
    async def set_maintenance_mode(self, enabled: bool) -> bool:
        """Set maintenance mode status in Redis"""
        try:
            if self.redis and self.redis.client:
                await self.redis.client.set("maintenance_mode", "1" if enabled else "0", ex=86400)
                return True
            return False
        except Exception as e:
            logger.error(f"Error setting maintenance mode: {e}")
            return False
    
    async def get_maintenance_mode(self) -> bool:
        """Check if maintenance mode is enabled"""
        try:
            if self.redis and self.redis.client:
                result = await self.redis.client.get("maintenance_mode")
                return result == b"1" or result == "1"
            return False
        except Exception as e:
            logger.error(f"Error checking maintenance mode: {e}")
            return False
    
    async def set_feature_toggle(self, feature: str, enabled: bool) -> bool:
        """Set feature toggle status in Redis"""
        try:
            if self.redis and self.redis.client:
                await self.redis.client.set(f"feature_{feature}", "1" if enabled else "0", ex=86400)
                return True
            return False
        except Exception as e:
            logger.error(f"Error setting feature toggle: {e}")
            return False
    
    async def get_feature_toggle(self, feature: str) -> bool:
        """Check if feature is enabled"""
        try:
            if self.redis and self.redis.client:
                result = await self.redis.client.get(f"feature_{feature}")
                return result == b"1" or result == "1"
            return True  # Default to enabled if Redis not available
        except Exception as e:
            logger.error(f"Error checking feature toggle: {e}")
            return True
    
    async def flush_redis_cache(self) -> bool:
        """Flush Redis cache"""
        try:
            if self.redis and self.redis.client:
                await self.redis.client.flushdb()
                logger.info("Redis cache flushed")
                return True
            return False
        except Exception as e:
            logger.error(f"Error flushing Redis cache: {e}")
            return False
    
    async def get_recent_logs(self, lines: int = 20) -> List[str]:
        """Get recent log lines"""
        try:
            import os
            log_file = "logs/bot.log"
            
            if not os.path.exists(log_file):
                return ["Log file not found"]
            
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if len(all_lines) > lines else all_lines
        except Exception as e:
            logger.error(f"Error reading logs: {e}")
            return [f"Error reading logs: {str(e)}"]
    
    async def get_error_logs(self, lines: int = 20) -> List[str]:
        """Get recent error log lines"""
        try:
            import os
            log_file = "logs/bot.log"
            
            if not os.path.exists(log_file):
                return ["Log file not found"]
            
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                # Filter for error lines
                error_lines = [line for line in all_lines if 'ERROR' in line or 'error' in line.lower()]
                return error_lines[-lines:] if len(error_lines) > lines else error_lines
        except Exception as e:
            logger.error(f"Error reading error logs: {e}")
            return [f"Error reading error logs: {str(e)}"]

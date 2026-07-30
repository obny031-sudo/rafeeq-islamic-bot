"""
Health Check Service for Rafeeq Enterprise Islamic OS.
Monitors PostgreSQL, Redis, and Telegram API connections.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from cache import RedisCache
from config.settings import settings
from utils.logger import get_logger

logger = get_logger("rafeeq.health_check")


class HealthStatus(str, Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Health status of a single component"""
    name: str
    status: HealthStatus
    message: str
    response_time_ms: Optional[float] = None
    last_checked: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "response_time_ms": self.response_time_ms,
            "last_checked": self.last_checked.isoformat() if self.last_checked else None
        }


class HealthCheckService:
    """
    Health check service for monitoring system components.
    Checks PostgreSQL, Redis, and Telegram API connections.
    """
    
    def __init__(
        self,
        bot: Bot,
        db_session_factory,
        redis_cache: RedisCache
    ):
        """
        Initialize health check service.
        
        Args:
            bot: Aiogram Bot instance
            db_session_factory: Database session factory
            redis_cache: Redis cache instance
        """
        self.bot = bot
        self.db_session_factory = db_session_factory
        self.redis_cache = redis_cache
        self._component_health: Dict[str, ComponentHealth] = {}
    
    async def check_postgresql(self) -> ComponentHealth:
        """
        Check PostgreSQL database connection.
        
        Returns:
            ComponentHealth with database status
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            async with self.db_session_factory() as session:
                # Execute a simple query to test connection
                result = await session.execute(text("SELECT 1"))
                result.fetchone()
            
            response_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            health = ComponentHealth(
                name="postgresql",
                status=HealthStatus.HEALTHY,
                message="Database connection successful",
                response_time_ms=response_time,
                last_checked=datetime.now(timezone.utc)
            )
            
            logger.debug(f"PostgreSQL health check: {response_time:.2f}ms")
            
        except Exception as e:
            health = ComponentHealth(
                name="postgresql",
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}",
                response_time_ms=None,
                last_checked=datetime.now(timezone.utc)
            )
            logger.error(f"PostgreSQL health check failed: {e}")
        
        self._component_health["postgresql"] = health
        return health
    
    async def check_redis(self) -> ComponentHealth:
        """
        Check Redis connection.
        
        Returns:
            ComponentHealth with Redis status
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            # Test Redis connection with PING
            if self.redis_cache._connected:
                await self.redis_cache.client.ping()
            else:
                await self.redis_cache.connect()
            
            response_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            health = ComponentHealth(
                name="redis",
                status=HealthStatus.HEALTHY,
                message="Redis connection successful",
                response_time_ms=response_time,
                last_checked=datetime.now(timezone.utc)
            )
            
            logger.debug(f"Redis health check: {response_time:.2f}ms")
            
        except Exception as e:
            health = ComponentHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                message=f"Redis connection failed: {str(e)}",
                response_time_ms=None,
                last_checked=datetime.now(timezone.utc)
            )
            logger.error(f"Redis health check failed: {e}")
        
        self._component_health["redis"] = health
        return health
    
    async def check_telegram_api(self) -> ComponentHealth:
        """
        Check Telegram API connection.
        
        Returns:
            ComponentHealth with Telegram API status
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            # Test Telegram API by getting bot info
            await self.bot.get_me()
            
            response_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            health = ComponentHealth(
                name="telegram_api",
                status=HealthStatus.HEALTHY,
                message="Telegram API connection successful",
                response_time_ms=response_time,
                last_checked=datetime.now(timezone.utc)
            )
            
            logger.debug(f"Telegram API health check: {response_time:.2f}ms")
            
        except Exception as e:
            health = ComponentHealth(
                name="telegram_api",
                status=HealthStatus.UNHEALTHY,
                message=f"Telegram API connection failed: {str(e)}",
                response_time_ms=None,
                last_checked=datetime.now(timezone.utc)
            )
            logger.error(f"Telegram API health check failed: {e}")
        
        self._component_health["telegram_api"] = health
        return health
    
    async def check_all(self) -> Dict[str, Any]:
        """
        Check all system components.
        
        Returns:
            Overall health status dictionary
        """
        logger.info("Running full health check...")
        
        # Check all components concurrently
        postgresql_health, redis_health, telegram_health = await asyncio.gather(
            self.check_postgresql(),
            self.check_redis(),
            self.check_telegram_api()
        )
        
        # Determine overall status
        all_healthy = all(
            health.status == HealthStatus.HEALTHY 
            for health in [postgresql_health, redis_health, telegram_health]
        )
        
        any_unhealthy = any(
            health.status == HealthStatus.UNHEALTHY 
            for health in [postgresql_health, redis_health, telegram_health]
        )
        
        if all_healthy:
            overall_status = HealthStatus.HEALTHY
        elif any_unhealthy:
            overall_status = HealthStatus.UNHEALTHY
        else:
            overall_status = HealthStatus.DEGRADED
        
        return {
            "overall_status": overall_status.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": {
                "postgresql": postgresql_health.to_dict(),
                "redis": redis_health.to_dict(),
                "telegram_api": telegram_health.to_dict()
            },
            "summary": {
                "total_components": 3,
                "healthy": sum(1 for h in [postgresql_health, redis_health, telegram_health] if h.status == HealthStatus.HEALTHY),
                "unhealthy": sum(1 for h in [postgresql_health, redis_health, telegram_health] if h.status == HealthStatus.UNHEALTHY),
                "degraded": sum(1 for h in [postgresql_health, redis_health, telegram_health] if h.status == HealthStatus.DEGRADED)
            }
        }
    
    def get_component_health(self, component_name: str) -> Optional[ComponentHealth]:
        """
        Get cached health status for a specific component.
        
        Args:
            component_name: Name of the component
        
        Returns:
            ComponentHealth or None if not checked yet
        """
        return self._component_health.get(component_name)
    
    async def get_health_summary(self) -> str:
        """
        Get a human-readable health summary.
        
        Returns:
            Formatted health summary string
        """
        health_data = await self.check_all()
        
        summary = f"🏥 *System Health Check*\n\n"
        summary += f"📊 *Overall Status:* {health_data['overall_status'].upper()}\n"
        summary += f"🕐 *Checked:* {health_data['timestamp']}\n\n"
        
        summary += "*Components:*\n"
        for component_name, component_data in health_data['components'].items():
            status_emoji = {
                'healthy': '✅',
                'degraded': '⚠️',
                'unhealthy': '❌',
                'unknown': '❓'
            }.get(component_data['status'], '❓')
            
            summary += f"{status_emoji} *{component_name.replace('_', ' ').title()}:* {component_data['status'].upper()}\n"
            if component_data['response_time_ms']:
                summary += f"   └ Response: {component_data['response_time_ms']:.2f}ms\n"
            summary += f"   └ {component_data['message']}\n"
        
        summary += f"\n*Summary:* {health_data['summary']['healthy']}/{health_data['summary']['total_components']} components healthy"
        
        return summary


# Global health check service instance (initialized in main.py)
health_check_service: Optional[HealthCheckService] = None


def get_health_check_service() -> HealthCheckService:
    """Get the global health check service instance."""
    if health_check_service is None:
        raise RuntimeError("Health check service not initialized. Call init_health_check_service() first.")
    return health_check_service


def init_health_check_service(
    bot: Bot,
    db_session_factory,
    redis_cache: RedisCache
) -> HealthCheckService:
    """
    Initialize the global health check service instance.
    
    Args:
        bot: Aiogram Bot instance
        db_session_factory: Database session factory
        redis_cache: Redis cache instance
    
    Returns:
        Initialized HealthCheckService instance
    """
    global health_check_service
    health_check_service = HealthCheckService(bot, db_session_factory, redis_cache)
    logger.info("Health check service initialized")
    return health_check_service

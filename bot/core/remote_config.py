"""
Remote Config System for Rafeeq Enterprise Islamic OS.
Allows dynamic configuration changes via Redis without restart.
"""

import logging
import json
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta

from cache import RedisCache
from config.settings import settings
from utils.logger import get_logger

logger = get_logger("rafeeq.remote_config")


class RemoteConfig:
    """
    Remote configuration manager using Redis.
    Allows runtime configuration changes without bot restart.
    """
    
    def __init__(self, cache: RedisCache):
        """
        Initialize remote config.
        
        Args:
            cache: Redis cache instance
        """
        self.cache = cache
        self._default_config: Dict[str, Any] = self._get_default_config()
        self._config_prefix = "config:"
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            # System limits
            "MAX_STREAK": 365,
            "API_TIMEOUT": 30,
            "RATE_LIMIT_MESSAGES_PER_SECOND": 30,
            "RATE_LIMIT_MESSAGES_PER_MINUTE": 20,
            
            # Plugin settings
            "PRAYER_CACHE_TTL": 3600,
            "QURAN_CACHE_TTL": 86400,
            "ADHKAR_CACHE_TTL": 3600,
            
            # User settings
            "DEFAULT_LANGUAGE": "en",
            "DEFAULT_TIMEZONE": "UTC",
            
            # Gamification
            "XP_PER_QURAN_AYAH": 1,
            "XP_PER_PRAYER": 5,
            "XP_PER_ADHKAR": 2,
            "STREAK_BONUS_MULTIPLIER": 1.5,
            
            # Notification settings
            "PRAYER_NOTIFICATION_ADVANCE_MINUTES": 5,
            "DAILY_ADHKAR_ENABLED": True,
            
            # Feature flags
            "AI_ASSISTANT_ENABLED": False,
            "VOICE_RECOGNITION_ENABLED": False,
            "SOCIAL_FEATURES_ENABLED": False,
        }
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
        
        Returns:
            Configuration value
        """
        cache_key = f"{self._config_prefix}{key}"
        
        # Try to get from Redis
        value = await self.cache.get(cache_key)
        
        if value is not None:
            logger.debug(f"Remote config hit: {key}")
            return value
        
        # Fall back to default
        default_value = self._default_config.get(key, default)
        logger.debug(f"Using default config: {key}")
        return default_value
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
            ttl: Time to live in seconds (None for permanent)
        
        Returns:
            True if successful, False otherwise
        """
        cache_key = f"{self._config_prefix}{key}"
        
        # Store in Redis
        success = await self.cache.set(cache_key, value, ttl)
        
        if success:
            logger.info(f"Remote config set: {key} = {value}")
        
        return success
    
    async def delete(self, key: str) -> bool:
        """
        Delete a configuration value (reverts to default).
        
        Args:
            key: Configuration key
        
        Returns:
            True if successful, False otherwise
        """
        cache_key = f"{self._config_prefix}{key}"
        success = await self.cache.delete(cache_key)
        
        if success:
            logger.info(f"Remote config deleted: {key} (reverted to default)")
        
        return success
    
    async def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration values (merged with defaults).
        
        Returns:
            Dictionary of all configuration values
        """
        config = {}
        
        # Start with defaults
        config.update(self._default_config)
        
        # Override with remote values
        for key in self._default_config.keys():
            cache_key = f"{self._config_prefix}{key}"
            value = await self.cache.get(cache_key)
            if value is not None:
                config[key] = value
        
        return config
    
    async def reset_to_defaults(self) -> bool:
        """
        Reset all remote configuration to defaults.
        
        Returns:
            True if successful
        """
        for key in self._default_config.keys():
            cache_key = f"{self._config_prefix}{key}"
            await self.cache.delete(cache_key)
        
        logger.info("All remote config reset to defaults")
        return True
    
    async def get_config_changes(self, since: datetime) -> Dict[str, Any]:
        """
        Get configuration changes since a specific time.
        
        Args:
            since: Datetime to check from
        
        Returns:
            Dictionary of changed values
        """
        # This would require storing change history
        # For now, return current config
        return await self.get_all()
    
    async def reload_config(self) -> Dict[str, Any]:
        """
        Reload configuration from Redis.
        
        Returns:
            Current configuration
        """
        return await self.get_all()
    
    async def set_batch(self, config_dict: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Set multiple configuration values at once.
        
        Args:
            config_dict: Dictionary of key-value pairs
            ttl: Time to live in seconds (None for permanent)
        
        Returns:
            True if successful
        """
        for key, value in config_dict.items():
            cache_key = f"{self._config_prefix}{key}"
            await self.cache.set(cache_key, value, ttl)
        
        logger.info(f"Batch remote config set: {len(config_dict)} keys")
        return True
    
    async def get_config_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current configuration state.
        
        Returns:
            Configuration summary
        """
        total_keys = len(self._default_config)
        remote_keys = 0
        
        for key in self._default_config.keys():
            cache_key = f"{self._config_prefix}{key}"
            if await self.cache.exists(cache_key):
                remote_keys += 1
        
        return {
            "total_keys": total_keys,
            "remote_keys": remote_keys,
            "default_keys": total_keys - remote_keys,
            "remote_percentage": round((remote_keys / total_keys) * 100, 2) if total_keys > 0 else 0
        }


class ConfigValidator:
    """Validates configuration values before setting them."""
    
    @staticmethod
    def validate_int(key: str, value: Any, min_val: int = 0, max_val: int = None) -> bool:
        """Validate integer configuration value."""
        try:
            int_value = int(value)
            if int_value < min_val:
                logger.warning(f"Config {key} value {int_value} below minimum {min_val}")
                return False
            if max_val is not None and int_value > max_val:
                logger.warning(f"Config {key} value {int_value} above maximum {max_val}")
                return False
            return True
        except (ValueError, TypeError):
            logger.error(f"Config {key} value {value} is not a valid integer")
            return False
    
    @staticmethod
    def validate_bool(key: str, value: Any) -> bool:
        """Validate boolean configuration value."""
        if isinstance(value, bool):
            return True
        if isinstance(value, str):
            return value.lower() in ('true', 'false', '1', '0')
        return False
    
    @staticmethod
    def validate_string(key: str, value: Any, allowed_values: List[str] = None) -> bool:
        """Validate string configuration value."""
        if not isinstance(value, str):
            logger.error(f"Config {key} value {value} is not a valid string")
            return False
        
        if allowed_values and value not in allowed_values:
            logger.warning(f"Config {key} value {value} not in allowed values: {allowed_values}")
            return False
        
        return True


# Global remote config instance (initialized in main.py)
remote_config: Optional[RemoteConfig] = None


def get_remote_config() -> RemoteConfig:
    """Get the global remote config instance."""
    if remote_config is None:
        raise RuntimeError("Remote config not initialized. Call init_remote_config() first.")
    return remote_config


async def init_remote_config(cache: RedisCache) -> RemoteConfig:
    """
    Initialize the global remote config instance.
    
    Args:
        cache: Redis cache instance
    
    Returns:
        Initialized RemoteConfig instance
    """
    global remote_config
    remote_config = RemoteConfig(cache)
    logger.info("Remote config initialized")
    return remote_config

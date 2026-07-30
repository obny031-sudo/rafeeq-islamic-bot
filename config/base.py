"""
Base configuration using Pydantic for hierarchical settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class BaseConfig(BaseSettings):
    """Base configuration class with common settings"""
    
    # Application
    APP_NAME: str = "Rafeeq"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    
    # Environment
    ENVIRONMENT: str = Field(default="production", env="ENVIRONMENT")
    
    model_config = SettingsConfigDict(env_file='.env', extra='ignore', env_file_encoding='utf-8', case_sensitive=False)


class DatabaseConfig(BaseSettings):
    """Database configuration"""
    
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://user:password@localhost/rafeeq",
        env="DATABASE_URL"
    )
    DATABASE_POOL_SIZE: int = Field(default=10, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")
    DATABASE_ECHO: bool = Field(default=False, env="DATABASE_ECHO")
    
    model_config = SettingsConfigDict(env_file='.env', extra='ignore', env_file_encoding='utf-8', case_sensitive=False)


class RedisConfig(BaseSettings):
    """Redis configuration"""
    
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )
    REDIS_FSM_DB: int = Field(default=0, env="REDIS_FSM_DB")
    REDIS_CACHE_DB: int = Field(default=1, env="REDIS_CACHE_DB")
    REDIS_SCHEDULER_DB: int = Field(default=2, env="REDIS_SCHEDULER_DB")
    
    model_config = SettingsConfigDict(env_file='.env', extra='ignore', env_file_encoding='utf-8', case_sensitive=False)


class BotConfig(BaseSettings):
    """Telegram Bot configuration"""
    
    BOT_TOKEN: str = Field(..., env="BOT_TOKEN")
    BOT_WEBHOOK_MODE: bool = Field(default=False, env="BOT_WEBHOOK_MODE")
    BOT_WEBHOOK_URL: Optional[str] = Field(default=None, env="BOT_WEBHOOK_URL")
    BOT_WEBHOOK_SECRET: Optional[str] = Field(default=None, env="BOT_WEBHOOK_SECRET")
    
    model_config = SettingsConfigDict(env_file='.env', extra='ignore', env_file_encoding='utf-8', case_sensitive=False)


class LoggingConfig(BaseSettings):
    """Logging configuration"""
    
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_DIR: str = Field(default="logs", env="LOG_DIR")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    LOG_MAX_BYTES: int = Field(default=10485760, env="LOG_MAX_BYTES")  # 10MB
    LOG_BACKUP_COUNT: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    model_config = SettingsConfigDict(env_file='.env', extra='ignore', env_file_encoding='utf-8', case_sensitive=False)

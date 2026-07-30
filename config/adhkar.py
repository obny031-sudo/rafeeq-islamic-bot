"""
Adhkar module configuration.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class AdhkarConfig(BaseSettings):
    """Adhkar module specific configuration"""
    
    # Default reminder time
    DEFAULT_MORNING_ADHKAR_TIME: str = Field(
        default="07:00",
        env="DEFAULT_MORNING_ADHKAR_TIME"
    )
    DEFAULT_EVENING_ADHKAR_TIME: str = Field(
        default="18:00",
        env="DEFAULT_EVENING_ADHKAR_TIME"
    )
    
    # Cache settings
    ADHKAR_CACHE_TTL: int = Field(default=3600, env="ADHKAR_CACHE_TTL")  # 1 hour
    
    model_config = SettingsConfigDict(env_file='.env', extra='ignore', env_file_encoding='utf-8', case_sensitive=False)

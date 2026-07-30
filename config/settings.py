"""
Main settings configuration - hierarchical Pydantic-based system.
"""

from pydantic import Field
from .base import BaseConfig, DatabaseConfig, RedisConfig, BotConfig, LoggingConfig
from .prayer import PrayerConfig
from .quran import QuranConfig
from .adhkar import AdhkarConfig


class Settings(BaseConfig, DatabaseConfig, RedisConfig, BotConfig, LoggingConfig):
    """
    Main settings class that inherits from all module-specific configurations.
    This provides a hierarchical configuration system.
    """
    
    # Module-specific configurations
    prayer: PrayerConfig = PrayerConfig()
    quran: QuranConfig = QuranConfig()
    adhkar: AdhkarConfig = AdhkarConfig()
    
    # OpenAI API
    OPENAI_API_KEY: str = Field(default=None, env="OPENAI_API_KEY")
    
    # Admin Configuration
    ADMIN_ID: int = Field(default=None, env="ADMIN_ID")
    
    # Application Settings
    DEFAULT_LANGUAGE: str = Field(default="ar", env="DEFAULT_LANGUAGE")
    SUPPORTED_LANGUAGES: list = Field(default=["ar"], env="SUPPORTED_LANGUAGES")
    DEFAULT_TIMEZONE: str = Field(default="Africa/Cairo", env="DEFAULT_TIMEZONE")
    
    def validate(self) -> bool:
        """Validate required settings"""
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is required in environment variables")
        return True


# Global settings instance
settings = Settings()

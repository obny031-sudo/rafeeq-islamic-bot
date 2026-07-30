"""
Prayer module configuration.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class PrayerConfig(BaseSettings):
    """Prayer module specific configuration"""
    
    # Aladhan API
    ALADHAN_API_URL: str = Field(
        default="https://api.aladhan.com/v1",
        env="ALADHAN_API_URL"
    )
    ALADHAN_API_TIMEOUT: int = Field(default=30, env="ALADHAN_API_TIMEOUT")
    
    # Default prayer calculation method
    DEFAULT_PRAYER_METHOD: int = Field(default=2, env="DEFAULT_PRAYER_METHOD")  # ISNA
    DEFAULT_ASR_METHOD: int = Field(default=0, env="DEFAULT_ASR_METHOD")  # Shafi
    
    # Default location (Cairo, Egypt)
    DEFAULT_LATITUDE: float = Field(default=30.0444, env="DEFAULT_LATITUDE")
    DEFAULT_LONGITUDE: float = Field(default=31.2357, env="DEFAULT_LONGITUDE")
    DEFAULT_TIMEZONE: str = Field(default="Africa/Cairo", env="DEFAULT_TIMEZONE")
    DEFAULT_CITY: str = Field(default="Cairo", env="DEFAULT_CITY")
    DEFAULT_COUNTRY: str = Field(default="Egypt", env="DEFAULT_COUNTRY")
    
    # Prayer notification settings
    PRAYER_NOTIFICATIONS_ENABLED: bool = Field(default=True, env="PRAYER_NOTIFICATIONS_ENABLED")
    PRAYER_NOTIFICATION_ADVANCE_MINUTES: int = Field(default=5, env="PRAYER_NOTIFICATION_ADVANCE_MINUTES")
    
    # Adhan audio settings
    ADHAN_AUDIO_ENABLED: bool = Field(default=True, env="ADHAN_AUDIO_ENABLED")
    ADHAN_AUDIO_PATH: str = Field(default="audio/adhan", env="ADHAN_AUDIO_PATH")
    
    # Cache settings
    PRAYER_CACHE_TTL: int = Field(default=3600, env="PRAYER_CACHE_TTL")  # 1 hour
    
    model_config = SettingsConfigDict(env_file='.env', extra='ignore', env_file_encoding='utf-8', case_sensitive=False)

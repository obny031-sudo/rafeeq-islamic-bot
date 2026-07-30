"""
Quran module configuration.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class QuranConfig(BaseSettings):
    """Quran module specific configuration"""
    
    # Quran API
    QURAN_API_URL: str = Field(
        default="https://api.alquran.cloud/v1",
        env="QURAN_API_URL"
    )
    QURAN_API_TIMEOUT: int = Field(default=30, env="QURAN_API_TIMEOUT")
    
    # Default edition
    DEFAULT_QURAN_EDITION: str = Field(
        default="quran-uthmani",
        env="DEFAULT_QURAN_EDITION"
    )
    DEFAULT_TRANSLATION_EDITION: str = Field(
        default="en.asad",
        env="DEFAULT_TRANSLATION_EDITION"
    )
    
    # Pagination settings
    SURAHS_PER_PAGE: int = Field(default=10, env="SURAHS_PER_PAGE")
    AYAHS_PER_PAGE: int = Field(default=5, env="AYAHS_PER_PAGE")
    
    # Cache settings
    QURAN_CACHE_TTL: int = Field(default=86400, env="QURAN_CACHE_TTL")  # 24 hours
    
    model_config = SettingsConfigDict(env_file='.env', extra='ignore', env_file_encoding='utf-8', case_sensitive=False)

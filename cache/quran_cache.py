"""
Quran-specific caching layer for hot data.
Caches Surah lists, Ayah data, and Tafsir to minimize API calls.
"""

import logging
from typing import Optional, Dict, Any
from cache.base import CacheBackend

logger = logging.getLogger(__name__)

class QuranCache:
    """Cache manager for Quran-related data"""
    
    def __init__(self, cache: CacheBackend):
        """
        Initialize Quran cache.
        
        Args:
            cache: Cache backend instance
        """
        self.cache = cache
        self.surah_list_ttl = 86400  # 24 hours - Surah list rarely changes
        self.surah_ayahs_ttl = 3600  # 1 hour - Ayah data
        self.tafsir_ttl = 86400  # 24 hours - Tafsir rarely changes
        self.translation_ttl = 86400  # 24 hours - Translations rarely changes
    
    async def get_surah_list(self) -> Optional[dict]:
        """Get cached Surah list"""
        key = "quran:surah_list"
        return await self.cache.get(key)
    
    async def set_surah_list(self, data: dict) -> bool:
        """Cache Surah list"""
        key = "quran:surah_list"
        return await self.cache.set(key, data, self.surah_list_ttl)
    
    async def get_surah_ayahs(self, surah_number: int, edition: str = "quran-uthmani") -> Optional[dict]:
        """Get cached Surah Ayahs"""
        key = f"quran:surah_{surah_number}_ayahs_{edition}"
        return await self.cache.get(key)
    
    async def set_surah_ayahs(self, surah_number: int, data: dict, edition: str = "quran-uthmani") -> bool:
        """Cache Surah Ayahs"""
        key = f"quran:surah_{surah_number}_ayahs_{edition}"
        return await self.cache.set(key, data, self.surah_ayahs_ttl)
    
    async def get_tafsir(self, surah_number: int, ayah_number: int, tafsir_edition: str = "ar.tafsir.ibnkathir") -> Optional[dict]:
        """Get cached Tafsir"""
        key = f"quran:tafsir_{tafsir_edition}_{surah_number}:{ayah_number}"
        return await self.cache.get(key)
    
    async def set_tafsir(self, surah_number: int, ayah_number: int, data: dict, tafsir_edition: str = "ar.tafsir.ibnkathir") -> bool:
        """Cache Tafsir"""
        key = f"quran:tafsir_{tafsir_edition}_{surah_number}:{ayah_number}"
        return await self.cache.set(key, data, self.tafsir_ttl)
    
    async def get_translation(self, surah_number: int, ayah_number: int, translation_edition: str = "en.sahih") -> Optional[dict]:
        """Get cached translation"""
        key = f"quran:translation_{translation_edition}_{surah_number}:{ayah_number}"
        return await self.cache.get(key)
    
    async def set_translation(self, surah_number: int, ayah_number: int, data: dict, translation_edition: str = "en.sahih") -> bool:
        """Cache translation"""
        key = f"quran:translation_{translation_edition}_{surah_number}:{ayah_number}"
        return await self.cache.set(key, data, self.translation_ttl)
    
    async def get_audio_url(self, surah_number: int, reciter: str = "ar.alafasy") -> Optional[str]:
        """Get cached audio URL"""
        key = f"quran:audio_{reciter}_surah_{surah_number}"
        return await self.cache.get(key)
    
    async def set_audio_url(self, surah_number: int, audio_url: str, reciter: str = "ar.alafasy") -> bool:
        """Cache audio URL"""
        key = f"quran:audio_{reciter}_surah_{surah_number}"
        return await self.cache.set(key, audio_url, self.surah_ayahs_ttl)
    
    async def invalidate_surah(self, surah_number: int) -> bool:
        """Invalidate all cached data for a specific Surah"""
        patterns = [
            f"quran:surah_{surah_number}_ayahs_*",
            f"quran:tafsir_*_{surah_number}:*",
            f"quran:translation_*_{surah_number}:*",
            f"quran:audio_*_surah_{surah_number}"
        ]
        
        # Note: This requires Redis pattern matching support
        # For now, we'll just invalidate the main Surah data
        key = f"quran:surah_{surah_number}_ayahs_quran-uthmani"
        return await self.cache.delete(key)

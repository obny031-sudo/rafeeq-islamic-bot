"""
Prayer-specific caching layer for hot data.
Caches prayer times, Qibla directions, and Hijri calendar data.
"""

import logging
from typing import Optional, Dict, Any
from cache.base import CacheBackend

logger = logging.getLogger(__name__)

class PrayerCache:
    """Cache manager for Prayer-related data"""
    
    def __init__(self, cache: CacheBackend):
        """
        Initialize Prayer cache.
        
        Args:
            cache: Cache backend instance
        """
        self.cache = cache
        self.prayer_times_ttl = 1800  # 30 minutes - Prayer times change daily
        self.qibla_ttl = 86400  # 24 hours - Qibla direction rarely changes
        self.hijri_ttl = 3600  # 1 hour - Hijri date changes daily
    
    async def get_prayer_times(self, latitude: float, longitude: float, 
                              method: int = 2, asr_method: int = 0, 
                              timezone: str = "UTC") -> Optional[dict]:
        """Get cached prayer times for a location"""
        key = f"prayer:times_{latitude:.4f}_{longitude:.4f}_{method}_{asr_method}_{timezone}"
        return await self.cache.get(key)
    
    async def set_prayer_times(self, latitude: float, longitude: float, data: dict,
                              method: int = 2, asr_method: int = 0, 
                              timezone: str = "UTC") -> bool:
        """Cache prayer times for a location"""
        key = f"prayer:times_{latitude:.4f}_{longitude:.4f}_{method}_{asr_method}_{timezone}"
        return await self.cache.set(key, data, self.prayer_times_ttl)
    
    async def get_qibla(self, latitude: float, longitude: float) -> Optional[dict]:
        """Get cached Qibla direction"""
        key = f"prayer:qibla_{latitude:.4f}_{longitude:.4f}"
        return await self.cache.get(key)
    
    async def set_qibla(self, latitude: float, longitude: float, data: dict) -> bool:
        """Cache Qibla direction"""
        key = f"prayer:qibla_{latitude:.4f}_{longitude:.4f}"
        return await self.cache.set(key, data, self.qibla_ttl)
    
    async def get_hijri_date(self, latitude: float, longitude: float, 
                           method: int = 2) -> Optional[dict]:
        """Get cached Hijri date"""
        key = f"prayer:hijri_{latitude:.4f}_{longitude:.4f}_{method}"
        return await self.cache.get(key)
    
    async def set_hijri_date(self, latitude: float, longitude: float, data: dict,
                           method: int = 2) -> bool:
        """Cache Hijri date"""
        key = f"prayer:hijri_{latitude:.4f}_{longitude:.4f}_{method}"
        return await self.cache.set(key, data, self.hijri_ttl)
    
    async def invalidate_location(self, latitude: float, longitude: float) -> bool:
        """Invalidate all cached data for a specific location"""
        patterns = [
            f"prayer:times_{latitude:.4f}_{longitude:.4f}_*",
            f"prayer:qibla_{latitude:.4f}_{longitude:.4f}",
            f"prayer:hijri_{latitude:.4f}_{longitude:.4f}_*"
        ]
        
        # Invalidate prayer times (most common)
        key = f"prayer:times_{latitude:.4f}_{longitude:.4f}_2_0_UTC"
        return await self.cache.delete(key)

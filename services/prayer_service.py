import logging
from datetime import datetime
from typing import Dict, Optional

from config.settings import settings
from services.http_client import ResilientHttpClient
from cache.prayer_cache import PrayerCache
from utils.shared_cache import shared_cache

logger = logging.getLogger(__name__)


class PrayerService:
    """Fetch prayer times from Aladhan API with retries."""

    def __init__(self):
        self.base_url = settings.prayer.ALADHAN_API_URL
        self.client = ResilientHttpClient(timeout=settings.prayer.ALADHAN_API_TIMEOUT)
        self.cache = PrayerCache(shared_cache)

    async def get_prayer_times(
        self,
        latitude: float,
        longitude: float,
        method: int = 2,
        asr_method: int = 0,
        timezone: str = "UTC",
    ) -> Optional[Dict]:
        # Try cache first
        cached = await self.cache.get_prayer_times(latitude, longitude, method, asr_method, timezone)
        if cached:
            return cached
        
        try:
            today = datetime.now().strftime("%d-%m-%Y")
            url = f"{self.base_url}/timings/{today}"
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "method": method,
                "school": asr_method,
                "timezone": timezone,
            }
            data = await self.client.get(url, params=params)
            if data and data.get("code") == 200:
                prayer_data = data.get("data")
                # Cache the result
                await self.cache.set_prayer_times(latitude, longitude, prayer_data, method, asr_method, timezone)
                return prayer_data
            return None
        except Exception as exc:
            logger.error("Error fetching prayer times: %s", exc)
            return None

    async def get_prayer_times_by_city(
        self,
        city: str,
        country: str,
        method: int = 2,
        asr_method: int = 0,
    ) -> Optional[Dict]:
        try:
            today = datetime.now().strftime("%d-%m-%Y")
            url = f"{self.base_url}/timingsByCity/{today}"
            params = {
                "city": city,
                "country": country,
                "method": method,
                "school": asr_method,
            }
            data = await self.client.get(url, params=params)
            if data and data.get("code") == 200:
                return data.get("data")
            return None
        except Exception as exc:
            logger.error("Error fetching prayer times by city: %s", exc)
            return None

    async def close(self):
        await self.client.close()


prayer_service = PrayerService()

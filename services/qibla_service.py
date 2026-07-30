"""Qibla direction and Hijri calendar service."""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from config.settings import settings
from services.http_client import ResilientHttpClient

logger = logging.getLogger(__name__)


class QiblaService:
    """Qibla and Hijri calendar via Aladhan API."""

    def __init__(self):
        self.base_url = settings.prayer.ALADHAN_API_URL
        self.client = ResilientHttpClient(timeout=settings.prayer.ALADHAN_API_TIMEOUT)

    async def get_qibla_direction(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        data = await self.client.get(f"{self.base_url}/qibla/{latitude}/{longitude}")
        if data and data.get("code") == 200:
            return data.get("data")
        return None

    async def get_hijri_calendar(self, month: Optional[int] = None, year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        today = datetime.now()
        month = month or today.month
        year = year or today.year
        data = await self.client.get(f"{self.base_url}/gToHCalendar/{month}/{year}")
        if data and data.get("code") == 200:
            return data.get("data")
        return None

    async def close(self) -> None:
        await self.client.close()


qibla_service = QiblaService()

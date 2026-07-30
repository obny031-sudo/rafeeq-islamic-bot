"""
Location-based prayer times handler - DISABLED.
All users now default to Cairo, Egypt (Lat: 30.0444, Lon: 31.2357, Timezone: Africa/Cairo).
Location sharing has been removed as per requirements.
"""

import logging
import httpx
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import User
from utils.redis_client import redis_client

logger = logging.getLogger(__name__)

router = Router()

# Default Cairo coordinates
CAIRO_LAT = 30.0444
CAIRO_LON = 31.2357
CAIRO_TIMEZONE = "Africa/Cairo"


async def get_cairo_prayer_times() -> dict:
    """
    Get prayer times for Cairo, Egypt using Aladhan API.
    
    Returns:
        Dictionary with prayer times or None
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"http://api.aladhan.com/v1/timings"
            
            params = {
                "latitude": CAIRO_LAT,
                "longitude": CAIRO_LON,
                "method": 2  # ISNA method
            }
            
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("code") == 200:
                return data.get("data", {})
            
            return None
            
    except Exception as e:
        logger.error(f"Error getting prayer times for Cairo: {e}")
        return None

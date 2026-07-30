"""
Tafseer (Quranic exegesis) handler.
Provides instant Tafseer for Quranic verses.
"""

import logging
import httpx
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

logger = logging.getLogger(__name__)

router = Router()

# Tafseer API endpoint (using a free Quran API)
TAFSEER_API_BASE = "http://api.alquran.cloud/v1"


@router.callback_query(F.data.startswith("tafseer_"))
async def handle_tafseer_request(callback: CallbackQuery):
    """Handle Tafseer request for a specific Ayah"""
    await callback.answer("جاري جلب التفسير...")
    
    # Parse callback data: tafseer_{surah}:{ayah}
    try:
        data_parts = callback.data.replace("tafseer_", "").split(":")
        surah_number = int(data_parts[0])
        ayah_number = int(data_parts[1])
        
        # Fetch Tafseer from API
        tafseer_text = await fetch_tafseer(surah_number, ayah_number)
        
        if tafseer_text:
            # Build response with Tafseer
            response_text = (
                f"📖 *تفسير الآية*\n\n"
                f"سورة {surah_number}، آية {ayah_number}\n\n"
                f"{tafseer_text}\n\n"
                f"المصدر: تفسير ابن كثير"
            )
            
            builder = InlineKeyboardBuilder()
            builder.row(
                InlineKeyboardButton(text="🔙 العودة", callback_data="quran_last_position")
            )
            
            await callback.message.edit_text(
                response_text,
                parse_mode="Markdown",
                reply_markup=builder.as_markup()
            )
        else:
            await callback.answer("❌ لم يتم العثور على التفسير", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error handling Tafseer request: {e}")
        await callback.answer("❌ خطأ في جلب التفسير", show_alert=True)


async def fetch_tafseer(surah_number: int, ayah_number: int) -> str:
    """
    Fetch Tafseer for a specific Ayah from API.
    
    Args:
        surah_number: Surah number (1-114)
        ayah_number: Ayah number within the Surah
    
    Returns:
        Tafseer text string
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Using AlQuran Cloud API for Tafseer
            url = f"{TAFSEER_API_BASE}/ayah/{surah_number}:{ayah_number}/editions/ar.ibnkathir"
            
            response = await client.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("code") == 200:
                tafseer_data = data.get("data", [])
                if tafseer_data:
                    # Get the Arabic Tafseer text
                    tafseer_edition = tafseer_data[0]
                    tafseer_text = tafseer_edition.get("text", "")
                    
                    # Clean up the text (remove Bismillah if present at start)
                    if tafseer_text.startswith("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"):
                        tafseer_text = tafseer_text.replace("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", "").strip()
                    
                    return tafseer_text[:2000]  # Limit length to avoid Telegram limits
            
            return None
            
    except Exception as e:
        logger.error(f"Error fetching Tafseer from API: {e}")
        return None


def get_tafseer_button(surah_number: int, ayah_number: int) -> InlineKeyboardButton:
    """
    Generate a Tafseer button for a specific Ayah.
    
    Args:
        surah_number: Surah number
        ayah_number: Ayah number
    
    Returns:
        InlineKeyboardButton for Tafseer
    """
    return InlineKeyboardButton(
        text="📚 التفسير",
        callback_data=f"tafseer_{surah_number}:{ayah_number}"
    )


async def get_tafseer_inline(surah_number: int, ayah_number: int) -> str:
    """
    Get Tafseer text inline (for use in other handlers).
    
    Args:
        surah_number: Surah number
        ayah_number: Ayah number
    
    Returns:
        Tafseer text string or None if not found
    """
    return await fetch_tafseer(surah_number, ayah_number)

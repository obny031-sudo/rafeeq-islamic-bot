"""
Adhan audio service for broadcasting prayer times with audio clips.
Supports multiple Qaris and manages audio file storage.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict
from aiogram import Bot
from aiogram.types import FSInputFile
from config.settings import settings

logger = logging.getLogger(__name__)


class AdhanService:
    """Service for managing Adhan audio clips and broadcasting"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.audio_path = Path(settings.prayer.ADHAN_AUDIO_PATH)
        self.ensure_audio_directory()
        
        # Available Qaris with their audio files
        self.qaris = {
            'abdul_basit': {
                'name': 'الشيخ عبد الباسط عبد الصمد',
                'files': {
                    'fajr': 'fajr_abdul_basit.mp3',
                    'dhuhr': 'dhuhr_abdul_basit.mp3',
                    'asr': 'asr_abdul_basit.mp3',
                    'maghrib': 'maghrib_abdul_basit.mp3',
                    'isha': 'isha_abdul_basit.mp3',
                }
            },
            'muhammad_rifat': {
                'name': 'الشيخ محمد رفعت',
                'files': {
                    'fajr': 'fajr_rifat.mp3',
                    'dhuhr': 'dhuhr_rifat.mp3',
                    'asr': 'asr_rifat.mp3',
                    'maghrib': 'maghrib_rifat.mp3',
                    'isha': 'isha_rifat.mp3',
                }
            },
            'mishary_rashid': {
                'name': 'الشيخ مشاري العفاسي',
                'files': {
                    'fajr': 'fajr_mishary.mp3',
                    'dhuhr': 'dhuhr_mishary.mp3',
                    'asr': 'asr_mishary.mp3',
                    'maghrib': 'maghrib_mishary.mp3',
                    'isha': 'isha_mishary.mp3',
                }
            }
        }
        
        # Default Qari
        self.default_qari = 'abdul_basit'
    
    def ensure_audio_directory(self):
        """Ensure audio directory exists"""
        self.audio_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Audio directory: {self.audio_path}")
    
    def get_audio_file(self, prayer: str, qari: Optional[str] = None) -> Optional[Path]:
        """Get audio file path for a specific prayer and Qari"""
        qari = qari or self.default_qari
        
        if qari not in self.qaris:
            logger.warning(f"Qari {qari} not found, using default")
            qari = self.default_qari
        
        qari_info = self.qaris[qari]
        filename = qari_info['files'].get(prayer)
        
        if not filename:
            logger.warning(f"No audio file for prayer {prayer} with Qari {qari}")
            return None
        
        audio_file = self.audio_path / filename
        
        if not audio_file.exists():
            logger.warning(f"Audio file not found: {audio_file}")
            return None
        
        return audio_file
    
    async def broadcast_adhan(
        self,
        chat_id: int,
        prayer: str,
        prayer_time: str,
        qari: Optional[str] = None,
        audio_enabled: bool = True
    ) -> bool:
        """
        Broadcast Adhan audio with notification to a user
        
        Args:
            chat_id: Telegram chat ID
            prayer: Prayer name (fajr, dhuhr, asr, maghrib, isha)
            prayer_time: Prayer time string
            qari: Qari name (optional, uses default if not specified)
            audio_enabled: Whether to send audio file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Arabic prayer names
            prayer_names = {
                'fajr': 'الفجر',
                'dhuhr': 'الظهر',
                'asr': 'العصر',
                'maghrib': 'المغرب',
                'isha': 'العشاء'
            }
            
            prayer_ar = prayer_names.get(prayer, prayer)
            
            # Send notification message
            notification_text = (
                f"🕌 *حان وقت صلاة {prayer_ar}*\n\n"
                f"⏰ *الوقت:* {prayer_time}\n"
                f"📍 *الموقع:* القاهرة، مصر\n\n"
                f"اللهم صلِّ على محمد وعلى آل محمد"
            )
            
            await self.bot.send_message(
                chat_id=chat_id,
                text=notification_text,
                parse_mode="Markdown"
            )
            
            # Send audio if enabled
            if audio_enabled and settings.prayer.ADHAN_AUDIO_ENABLED:
                audio_file = self.get_audio_file(prayer, qari)
                
                if audio_file:
                    audio = FSInputFile(audio_file)
                    await self.bot.send_audio(
                        chat_id=chat_id,
                        audio=audio,
                        caption=f"🎙️ الأذان - {self.qaris[qari or self.default_qari]['name']}"
                    )
                    logger.info(f"Sent Adhan audio for {prayer} to user {chat_id}")
                else:
                    logger.warning(f"Audio file not available for {prayer}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error broadcasting Adhan: {e}")
            return False
    
    def get_available_qaris(self) -> Dict[str, str]:
        """Get list of available Qaris"""
        return {key: info['name'] for key, info in self.qaris.items()}
    
    def check_audio_files(self) -> Dict[str, bool]:
        """Check which audio files exist"""
        status = {}
        
        for qari_key, qari_info in self.qaris.items():
            for prayer, filename in qari_info['files'].items():
                audio_file = self.audio_path / filename
                status[f"{qari_key}_{prayer}"] = audio_file.exists()
        
        return status


# Global instance (will be initialized with bot)
adhan_service: Optional[AdhanService] = None


def get_adhan_service(bot: Bot) -> AdhanService:
    """Get or create Adhan service instance"""
    global adhan_service
    if adhan_service is None:
        adhan_service = AdhanService(bot)
    return adhan_service

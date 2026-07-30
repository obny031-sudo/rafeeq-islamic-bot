"""
Test script for triggering daily broadcast notifications manually.
This script allows testing the automated daily spiritual reminders system.
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Bot
from config.settings import settings
from services.scheduler_service import scheduler_service


async def test_daily_broadcasts(user_id: int):
    """Test all daily broadcast functions for a specific user"""
    
    # Initialize bot
    bot = Bot(token=settings.BOT_TOKEN)
    scheduler_service.set_bot(bot)
    
    print(f"🧪 Starting daily broadcast test for user {user_id}...")
    print("=" * 50)
    
    try:
        # Test 1: Morning broadcast (Ayah + Morning Adhkar)
        print("🌅 Testing Morning Broadcast (Ayah + Morning Adhkar)...")
        await scheduler_service._send_morning_adhkar(user_id)
        print("✅ Morning broadcast sent!")
        await asyncio.sleep(2)
        
        # Test 2: Noon broadcast (Daily Hadith)
        print("☀️ Testing Noon Broadcast (Daily Hadith)...")
        await scheduler_service._send_daily_hadith(user_id)
        print("✅ Noon broadcast sent!")
        await asyncio.sleep(2)
        
        # Test 3: Afternoon/Evening broadcast (Wisdom + Evening Adhkar)
        print("🌆 Testing Afternoon Broadcast (Wisdom + Evening Adhkar)...")
        await scheduler_service._send_daily_wisdom(user_id)
        print("✅ Afternoon broadcast sent!")
        await asyncio.sleep(2)
        
        # Test 4: Night broadcast (Duaa + Sleep Adhkar)
        print("🌙 Testing Night Broadcast (Duaa + Sleep Adhkar)...")
        await scheduler_service._send_daily_duaa(user_id)
        print("✅ Night broadcast sent!")
        
        print("=" * 50)
        print("🎉 All daily broadcast tests completed successfully!")
        print(f"📱 Please check your Telegram chat (ID: {user_id}) for the messages.")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await bot.session.close()


if __name__ == "__main__":
    # Get user ID from command line or use default
    if len(sys.argv) > 1:
        test_user_id = int(sys.argv[1])
    else:
        # Default to admin ID or ask for input
        test_user_id = settings.ADMIN_ID if settings.ADMIN_ID else input("Enter your Telegram user ID: ")
    
    asyncio.run(test_daily_broadcasts(test_user_id))

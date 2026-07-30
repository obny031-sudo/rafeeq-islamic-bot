"""
Script to purge fake/generated data from database.
This removes all seeded data that was auto-generated.
"""

import asyncio
import sys
sys.path.insert(0, 'd:/Rafeeq')

from config.database import AsyncSessionLocal
from sqlalchemy import delete
from models.content import QuranAyah, Hadith, IslamicTip, Dua, Adhkar


async def purge_fake_data():
    """Delete all fake/generated data from database"""
    async with AsyncSessionLocal() as session:
        try:
            # Delete all fake Quran Ayahs
            await session.execute(delete(QuranAyah))
            print("✅ Deleted all Quran Ayahs")
            
            # Delete all fake Hadiths
            await session.execute(delete(Hadith))
            print("✅ Deleted all Hadiths")
            
            # Delete all fake Islamic Tips
            await session.execute(delete(IslamicTip))
            print("✅ Deleted all Islamic Tips")
            
            # Delete all fake Duas
            await session.execute(delete(Dua))
            print("✅ Deleted all Duas")
            
            # Delete all fake Adhkar
            await session.execute(delete(Adhkar))
            print("✅ Deleted all Adhkar")
            
            await session.commit()
            print("\n🎉 All fake data purged successfully!")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error purging data: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(purge_fake_data())

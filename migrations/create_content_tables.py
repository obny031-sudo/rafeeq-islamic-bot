"""
Migration script to create content tables for Islamic content storage.
Creates tables for Quran, Adhkar, Hadiths, Tips, Duas, Allah's Names, Stories, and Fiqh Q&A.
"""

import sys
import os
import asyncio
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

import asyncpg
from config.settings import settings


async def create_content_tables():
    """Create all content tables for Islamic content"""
    
    # Get DATABASE_URL and convert to asyncpg format
    database_url = settings.DATABASE_URL
    dsn = database_url.replace("postgresql+asyncpg://", "postgresql://")
    
    conn = await asyncpg.connect(dsn)
    
    try:
        # Drop existing tables if they exist (to ensure clean schema)
        tables_to_drop = [
            'user_notification_preferences',
            'fiqh_qa',
            'prophetic_stories',
            'allah_names',
            'duas',
            'islamic_tips',
            'hadiths',
            'adhkar',
            'quran_ayahs'
        ]
        
        for table in tables_to_drop:
            await conn.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
        
        # Create Quran Ayahs table
        await conn.execute("""
            CREATE TABLE quran_ayahs (
                id SERIAL PRIMARY KEY,
                surah_number INTEGER NOT NULL,
                ayah_number INTEGER NOT NULL,
                ayah_number_in_surah INTEGER NOT NULL,
                arabic_text TEXT NOT NULL,
                translation_en TEXT,
                translation_ar TEXT,
                tafsir_ar TEXT,
                tafsir_en TEXT,
                surah_name_ar VARCHAR(100),
                surah_name_en VARCHAR(100),
                surah_type VARCHAR(20),
                ayahs_count INTEGER,
                juz_number INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create indexes for Quran
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_surah_ayah ON quran_ayahs(surah_number, ayah_number_in_surah);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_juz ON quran_ayahs(juz_number);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_quran_surah ON quran_ayahs(surah_number);")
        
        # Create Adhkar table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS adhkar (
                id SERIAL PRIMARY KEY,
                category VARCHAR(50) NOT NULL,
                arabic_text TEXT NOT NULL,
                transliteration TEXT,
                translation_ar TEXT,
                translation_en TEXT,
                reference VARCHAR(200),
                count INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_category ON adhkar(category);")
        
        # Create Hadiths table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS hadiths (
                id SERIAL PRIMARY KEY,
                collection VARCHAR(50) NOT NULL,
                book_number INTEGER,
                hadith_number INTEGER,
                arabic_text TEXT NOT NULL,
                translation_en TEXT,
                translation_ar TEXT,
                narrator VARCHAR(200),
                grade VARCHAR(50),
                explanation_ar TEXT,
                explanation_en TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_collection ON hadiths(collection);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_grade ON hadiths(grade);")
        
        # Create Islamic Tips table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS islamic_tips (
                id SERIAL PRIMARY KEY,
                category VARCHAR(50) NOT NULL,
                title_ar VARCHAR(200),
                title_en VARCHAR(200),
                content_ar TEXT NOT NULL,
                content_en TEXT,
                reference VARCHAR(200),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_tip_category ON islamic_tips(category);")
        
        # Create Duas table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS duas (
                id SERIAL PRIMARY KEY,
                category VARCHAR(50) NOT NULL,
                source VARCHAR(50),
                arabic_text TEXT NOT NULL,
                transliteration TEXT,
                translation_ar TEXT,
                translation_en TEXT,
                reference VARCHAR(200),
                occasion_ar TEXT,
                occasion_en TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_dua_category ON duas(category);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_dua_source ON duas(source);")
        
        # Create Allah's Names table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS allah_names (
                id SERIAL PRIMARY KEY,
                name_ar VARCHAR(100) UNIQUE NOT NULL,
                name_en VARCHAR(100) UNIQUE,
                transliteration VARCHAR(100),
                meaning_ar TEXT,
                meaning_en TEXT,
                significance_ar TEXT,
                significance_en TEXT,
                when_to_say_ar TEXT,
                when_to_say_en TEXT,
                reference VARCHAR(200),
                number INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_name_number ON allah_names(number);")
        
        # Create Prophetic Stories table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS prophetic_stories (
                id SERIAL PRIMARY KEY,
                category VARCHAR(50) NOT NULL,
                subject VARCHAR(100) NOT NULL,
                title_ar VARCHAR(200),
                title_en VARCHAR(200),
                story_ar TEXT NOT NULL,
                story_en TEXT,
                lessons_ar TEXT,
                lessons_en TEXT,
                reference VARCHAR(200),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_story_category ON prophetic_stories(category);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_story_subject ON prophetic_stories(subject);")
        
        # Create Fiqh Q&A table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS fiqh_qa (
                id SERIAL PRIMARY KEY,
                category VARCHAR(50) NOT NULL,
                question_ar TEXT NOT NULL,
                question_en TEXT,
                answer_ar TEXT NOT NULL,
                answer_en TEXT,
                source VARCHAR(200),
                reference VARCHAR(200),
                difficulty VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_fiqh_category ON fiqh_qa(category);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_fiqh_difficulty ON fiqh_qa(difficulty);")
        
        # Create User Notification Preferences table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_notification_preferences (
                id SERIAL PRIMARY KEY,
                user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                morning_adhkar_enabled BOOLEAN DEFAULT TRUE,
                evening_adhkar_enabled BOOLEAN DEFAULT TRUE,
                night_adhkar_enabled BOOLEAN DEFAULT TRUE,
                friday_surah_enabled BOOLEAN DEFAULT TRUE,
                daily_ayah_enabled BOOLEAN DEFAULT TRUE,
                daily_hadith_enabled BOOLEAN DEFAULT TRUE,
                daily_tip_enabled BOOLEAN DEFAULT TRUE,
                daily_dua_enabled BOOLEAN DEFAULT TRUE,
                prayer_notifications_enabled BOOLEAN DEFAULT TRUE,
                adhan_audio_enabled BOOLEAN DEFAULT TRUE,
                morning_adhkar_time VARCHAR(5) DEFAULT '06:00',
                evening_adhkar_time VARCHAR(5) DEFAULT '17:00',
                night_adhkar_time VARCHAR(5) DEFAULT '22:30',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_user_notif_prefs ON user_notification_preferences(user_id);")
        
        # Create trigger for updated_at
        for table in ['quran_ayahs', 'adhkar', 'hadiths', 'islamic_tips', 'duas', 'allah_names', 'prophetic_stories', 'fiqh_qa', 'user_notification_preferences']:
            await conn.execute(f"""
                CREATE OR REPLACE FUNCTION update_{table}_updated_at()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
                
                DROP TRIGGER IF EXISTS trigger_update_{table}_updated_at ON {table};
                CREATE TRIGGER trigger_update_{table}_updated_at
                BEFORE UPDATE ON {table}
                FOR EACH ROW
                EXECUTE FUNCTION update_{table}_updated_at();
            """)
        
        print("✅ All content tables created successfully!")
        print("Created tables:")
        print("  - quran_ayahs")
        print("  - adhkar")
        print("  - hadiths")
        print("  - islamic_tips")
        print("  - duas")
        print("  - allah_names")
        print("  - prophetic_stories")
        print("  - fiqh_qa")
        print("  - user_notification_preferences")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(create_content_tables())

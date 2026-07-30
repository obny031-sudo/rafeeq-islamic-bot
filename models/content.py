"""
Content database models for Islamic content storage.
Includes models for Quran, Adhkar, Hadiths, Tips, Duas, Allah's Names, Stories, and Fiqh Q&A.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from models.base import Base


class QuranAyah(Base):
    """Quranic Ayah model - stores 6,236 verses of the Quran"""
    __tablename__ = "quran_ayahs"
    
    id = Column(Integer, primary_key=True, index=True)
    surah_number = Column(Integer, nullable=False, index=True)
    ayah_number = Column(Integer, nullable=False)
    ayah_number_in_surah = Column(Integer, nullable=False)
    
    # Arabic text
    arabic_text = Column(Text, nullable=False)
    
    # Translation
    translation_en = Column(Text)
    translation_ar = Column(Text)
    
    # Tafsir (explanation)
    tafsir_ar = Column(Text)
    tafsir_en = Column(Text)
    
    # Surah info
    surah_name_ar = Column(String(100))
    surah_name_en = Column(String(100))
    surah_type = Column(String(20))  # Meccan/Medinan
    ayahs_count = Column(Integer)
    
    # Juz info
    juz_number = Column(Integer)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Composite index for efficient queries
    __table_args__ = (
        Index('idx_surah_ayah', 'surah_number', 'ayah_number_in_surah'),
        Index('idx_juz', 'juz_number'),
    )


class Adhkar(Base):
    """Adhkar model - stores 1,000+ daily remembrances and supplications"""
    __tablename__ = "adhkar"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Category
    category = Column(String(50), nullable=False, index=True)  # morning, evening, sleep, post_prayer, travel, mosque, general
    
    # Arabic text
    arabic_text = Column(Text, nullable=False)
    transliteration = Column(Text)
    
    # Translation
    translation_ar = Column(Text)
    translation_en = Column(Text)
    
    # Reference
    reference = Column(String(200))
    
    # Count (for repeated dhikr)
    count = Column(Integer, default=1)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_category', 'category'),
    )


class Hadith(Base):
    """Hadith model - stores 1,000+ authentic hadiths"""
    __tablename__ = "hadiths"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Collection
    collection = Column(String(50), nullable=False, index=True)  # bukhari, muslim, tirmidhi, etc.
    book_number = Column(Integer)
    hadith_number = Column(Integer)
    
    # Arabic text
    arabic_text = Column(Text, nullable=False)
    
    # Translation
    translation_en = Column(Text)
    translation_ar = Column(Text)
    
    # Narrator (Rawi)
    narrator = Column(String(200))
    
    # Grade/Authentication
    grade = Column(String(50))  # Sahih, Hasan, Da'if
    
    # Explanation
    explanation_ar = Column(Text)
    explanation_en = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_collection', 'collection'),
        Index('idx_grade', 'grade'),
    )


class IslamicTip(Base):
    """Islamic Tips & Wisdom model - stores 1,000+ tips and spiritual advice"""
    __tablename__ = "islamic_tips"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Category
    category = Column(String(50), nullable=False, index=True)  # spiritual, practical, social, etc.
    
    # Content
    title_ar = Column(String(200))
    title_en = Column(String(200))
    content_ar = Column(Text, nullable=False)
    content_en = Column(Text)
    
    # Reference
    reference = Column(String(200))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_tip_category', 'category'),
    )


class Dua(Base):
    """Dua model - stores 1,000+ supplications from Quran and Sunnah"""
    __tablename__ = "duas"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Category
    category = Column(String(50), nullable=False, index=True)  # morning, evening, difficulty, gratitude, etc.
    source = Column(String(50))  # quran, hadith, general
    
    # Arabic text
    arabic_text = Column(Text, nullable=False)
    transliteration = Column(Text)
    
    # Translation
    translation_ar = Column(Text)
    translation_en = Column(Text)
    
    # Reference
    reference = Column(String(200))  # Surah:Ayah or Hadith reference
    
    # When to say
    occasion_ar = Column(Text)
    occasion_en = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_dua_category', 'category'),
        Index('idx_dua_source', 'source'),
    )


class AllahName(Base):
    """Allah's Names & Attributes model - stores 1,000+ names and attributes"""
    __tablename__ = "allah_names"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Name
    name_ar = Column(String(100), nullable=False, unique=True)
    name_en = Column(String(100), unique=True)
    transliteration = Column(String(100))
    
    # Meaning
    meaning_ar = Column(Text)
    meaning_en = Column(Text)
    
    # Spiritual significance
    significance_ar = Column(Text)
    significance_en = Column(Text)
    
    # When to say
    when_to_say_ar = Column(Text)
    when_to_say_en = Column(Text)
    
    # Reference
    reference = Column(String(200))
    
    # Number (for the 99 names)
    number = Column(Integer)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_name_number', 'number'),
    )


class PropheticStory(Base):
    """Prophets & Companions Stories model - stores 1,000+ stories and lessons"""
    __tablename__ = "prophetic_stories"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Category
    category = Column(String(50), nullable=False, index=True)  # prophet, companion, general
    subject = Column(String(100), nullable=False, index=True)  # Muhammad, Ibrahim, Abu Bakr, etc.
    
    # Content
    title_ar = Column(String(200))
    title_en = Column(String(200))
    story_ar = Column(Text, nullable=False)
    story_en = Column(Text)
    
    # Lessons
    lessons_ar = Column(Text)
    lessons_en = Column(Text)
    
    # Reference
    reference = Column(String(200))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_story_category', 'category'),
        Index('idx_story_subject', 'subject'),
    )


class FiqhQA(Base):
    """Fiqh Q&A model - stores 1,000+ simplified Fiqh questions and answers"""
    __tablename__ = "fiqh_qa"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Category
    category = Column(String(50), nullable=False, index=True)  # purification, prayer, fasting, zakat, hajj, etc.
    
    # Question
    question_ar = Column(Text, nullable=False)
    question_en = Column(Text)
    
    # Answer
    answer_ar = Column(Text, nullable=False)
    answer_en = Column(Text)
    
    # Source/Reference
    source = Column(String(200))  # madhab, scholar, etc.
    reference = Column(String(200))
    
    # Difficulty level
    difficulty = Column(String(20))  # beginner, intermediate, advanced
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_fiqh_category', 'category'),
        Index('idx_fiqh_difficulty', 'difficulty'),
    )


class UserNotificationPreference(Base):
    """User notification preferences model"""
    __tablename__ = "user_notification_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    
    # Notification toggles
    morning_adhkar_enabled = Column(Boolean, default=True)
    evening_adhkar_enabled = Column(Boolean, default=True)
    night_adhkar_enabled = Column(Boolean, default=True)
    
    friday_surah_enabled = Column(Boolean, default=True)
    
    daily_ayah_enabled = Column(Boolean, default=True)
    daily_hadith_enabled = Column(Boolean, default=True)
    daily_tip_enabled = Column(Boolean, default=True)
    daily_dua_enabled = Column(Boolean, default=True)
    
    prayer_notifications_enabled = Column(Boolean, default=True)
    adhan_audio_enabled = Column(Boolean, default=True)
    
    # Notification times (user can customize)
    morning_adhkar_time = Column(String(5), default="06:00")  # HH:MM format
    evening_adhkar_time = Column(String(5), default="17:00")
    night_adhkar_time = Column(String(5), default="22:30")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="notification_preferences")

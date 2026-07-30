from sqlalchemy import Column, Integer, BigInteger, String, Float, DateTime, Boolean, Enum as SQLEnum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum
from .base import Base

class Language(str, Enum):
    ENGLISH = "en"
    ARABIC = "ar"

class Role(str, Enum):
    USER = "user"
    PREMIUM = "premium"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class User(Base):
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True, index=True)  # Telegram User ID
    username = Column(String(100), nullable=True, index=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    
    # Location
    latitude = Column(Float, nullable=True, index=True)
    longitude = Column(Float, nullable=True, index=True)
    city = Column(String(100), nullable=True, index=True)
    country = Column(String(100), nullable=True, index=True)
    
    # Preferences
    language = Column(SQLEnum(Language), default=Language.ARABIC, index=True)
    timezone = Column(String(50), default="Africa/Cairo")
    role = Column(SQLEnum(Role), default=Role.USER, index=True)
    
    # Streak and Progress
    streak_days = Column(Integer, default=0)
    last_active_date = Column(DateTime(timezone=True), nullable=True, index=True)
    total_quran_read = Column(Integer, default=0)  # Ayahs read
    memorization_progress = Column(Integer, default=0)  # Percentage
    
    # Quran Reading
    last_read_surah = Column(Integer, nullable=True, index=True)  # Last read Surah number (1-114)
    last_read_ayah = Column(Integer, nullable=True)  # Last read Ayah number
    
    # Prayer Settings
    prayer_method = Column(Integer, default=2, index=True)  # Aladhan API method (2: ISNA)
    asr_method = Column(Integer, default=0)  # 0: Shafi, 1: Hanafi
    
    # Notifications
    prayer_notifications_enabled = Column(Boolean, default=True, index=True)
    daily_wird_enabled = Column(Boolean, default=True, index=True)
    
    # Admin/Ban fields
    is_banned = Column(Boolean, default=False, index=True)
    ban_reason = Column(String(500), nullable=True)
    banned_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, language={self.language})>"

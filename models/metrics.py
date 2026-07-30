"""
Metrics models for tracking usage, streaks, and achievements.
"""

from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.sql import func
from models.base import Base


class UserMetrics(Base):
    """User-specific metrics tracking"""
    __tablename__ = "user_metrics"
    
    id = Column(BigInteger, primary_key=True, index=True)  # Telegram User ID
    total_messages = Column(Integer, default=0)
    quran_ayahs_read = Column(Integer, default=0)
    prayers_completed = Column(Integer, default=0)
    adhkar_completed = Column(Integer, default=0)
    memorization_sessions = Column(Integer, default=0)
    
    # Engagement metrics
    session_count = Column(Integer, default=0)
    total_session_duration = Column(Integer, default=0)  # in seconds
    
    # Achievement tracking
    achievements_unlocked = Column(Integer, default=0)
    xp_points = Column(Integer, default=0)
    level = Column(Integer, default=1)
    
    # Timestamps
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<UserMetrics(id={self.id}, level={self.level}, xp={self.xp_points})>"


class ModuleUsage(Base):
    """Module-specific usage tracking"""
    __tablename__ = "module_usage"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), index=True)
    module_name = Column(String(50), index=True)
    action = Column(String(100))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<ModuleUsage(user_id={self.user_id}, module={self.module_name}, action={self.action})>"


class Achievement(Base):
    """Achievement definitions"""
    __tablename__ = "achievements"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(500))
    category = Column(String(50))  # quran, prayer, streak, etc.
    xp_reward = Column(Integer, default=0)
    requirement_type = Column(String(50))  # count, streak, etc.
    requirement_value = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<Achievement(name={self.name}, xp={self.xp_reward})>"


class UserAchievement(Base):
    """User achievement progress"""
    __tablename__ = "user_achievements"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), index=True)
    achievement_id = Column(Integer, ForeignKey("achievements.id"))
    progress = Column(Integer, default=0)
    unlocked = Column(Boolean, default=False)
    unlocked_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<UserAchievement(user_id={self.user_id}, achievement_id={self.achievement_id}, unlocked={self.unlocked})>"

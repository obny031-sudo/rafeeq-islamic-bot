"""
Simple and Reliable Notification System for Rafeeq Bot

This is a straightforward notification scheduler that:
- Sends notifications at the right time
- Prevents duplicate notifications
- Has basic retry mechanism
- Logs delivery status
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from sqlalchemy import create_engine
import pytz

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database for job persistence (SQLite for simplicity)
DB_URL = 'sqlite:///notifications.db'
jobstores = {
    'default': SQLAlchemyJobStore(url=DB_URL)
}

# Initialize scheduler
scheduler = AsyncIOScheduler(jobstores=jobstores, timezone=pytz.UTC)

# Notification tracking to prevent duplicates
notification_history = {}  # In-memory cache for recent notifications


class NotificationSystem:
    """Simple notification system with reliability features"""
    
    def __init__(self):
        self.scheduler = scheduler
        self.bot = None  # Will be set when bot is initialized
        
    def set_bot(self, bot):
        """Set the bot instance for sending notifications"""
        self.bot = bot
        
    def start(self):
        """Start the notification scheduler"""
        try:
            self.scheduler.start()
            logger.info("Notification system started successfully")
        except Exception as e:
            logger.error(f"Failed to start notification system: {e}")
            
    def stop(self):
        """Stop the notification scheduler"""
        try:
            self.scheduler.shutdown()
            logger.info("Notification system stopped")
        except Exception as e:
            logger.error(f"Failed to stop notification system: {e}")
    
    def schedule_prayer_notification(
        self,
        user_id: int,
        prayer_name: str,
        prayer_time: str,
        timezone: str = 'Africa/Cairo'
    ):
        """Schedule a prayer time notification for a user"""
        try:
            # Create unique job ID to prevent duplicates
            job_id = f"prayer_{user_id}_{prayer_name}_{datetime.now().strftime('%Y%m%d')}"
            
            # Check if job already exists
            if self.scheduler.get_job(job_id):
                logger.info(f"Prayer notification already scheduled: {job_id}")
                return False
            
            # Parse prayer time (format: "HH:MM")
            hour, minute = map(int, prayer_time.split(':'))
            
            # Schedule the job
            self.scheduler.add_job(
                self.send_prayer_notification,
                trigger=CronTrigger(hour=hour, minute=minute, timezone=timezone),
                id=job_id,
                args=[user_id, prayer_name],
                replace_existing=False,
                max_instances=1
            )
            
            logger.info(f"Scheduled prayer notification: {job_id} at {prayer_time}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to schedule prayer notification: {e}")
            return False
    
    async def send_prayer_notification(self, user_id: int, prayer_name: str):
        """Send prayer notification to user"""
        try:
            if not self.bot:
                logger.error("Bot not initialized, cannot send notification")
                return False
            
            # Check for duplicate (recent notification)
            notification_key = f"{user_id}_{prayer_name}_{datetime.now().strftime('%Y%m%d')}"
            if notification_key in notification_history:
                logger.info(f"Duplicate notification prevented: {notification_key}")
                return False
            
            # Send notification
            message = f"⏰ حان وقت صلاة {prayer_name}\n\nلا تنس الصلاة في وقتها 🕌"
            
            # Retry mechanism (3 attempts)
            for attempt in range(3):
                try:
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode='HTML'
                    )
                    
                    # Mark as sent
                    notification_history[notification_key] = datetime.now()
                    logger.info(f"Prayer notification sent successfully: {notification_key}")
                    
                    # Clean up old entries (keep last 24 hours)
                    self._cleanup_notification_history()
                    
                    return True
                    
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    if attempt < 2:  # Don't sleep after last attempt
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff: 2s, 4s
            
            logger.error(f"Failed to send prayer notification after 3 attempts: {notification_key}")
            return False
            
        except Exception as e:
            logger.error(f"Error in send_prayer_notification: {e}")
            return False
    
    def _cleanup_notification_history(self):
        """Clean up old notification history entries"""
        try:
            cutoff = datetime.now() - timedelta(hours=24)
            keys_to_remove = [
                key for key, timestamp in notification_history.items()
                if timestamp < cutoff
            ]
            for key in keys_to_remove:
                del notification_history[key]
        except Exception as e:
            logger.error(f"Error cleaning up notification history: {e}")
    
    def schedule_daily_reminder(
        self,
        user_id: int,
        reminder_type: str,
        time: str,
        message: str,
        timezone: str = 'Africa/Cairo'
    ):
        """Schedule a daily reminder for meditation, Quran reading, etc."""
        try:
            job_id = f"daily_{user_id}_{reminder_type}"
            
            # Check if job already exists
            if self.scheduler.get_job(job_id):
                logger.info(f"Daily reminder already scheduled: {job_id}")
                return False
            
            hour, minute = map(int, time.split(':'))
            
            self.scheduler.add_job(
                self.send_daily_reminder,
                trigger=CronTrigger(hour=hour, minute=minute, timezone=timezone),
                id=job_id,
                args=[user_id, reminder_type, message],
                replace_existing=False,
                max_instances=1
            )
            
            logger.info(f"Scheduled daily reminder: {job_id} at {time}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to schedule daily reminder: {e}")
            return False
    
    async def send_daily_reminder(self, user_id: int, reminder_type: str, message: str):
        """Send daily reminder to user"""
        try:
            if not self.bot:
                logger.error("Bot not initialized, cannot send reminder")
                return False
            
            # Check for duplicate
            notification_key = f"{user_id}_{reminder_type}_{datetime.now().strftime('%Y%m%d')}"
            if notification_key in notification_history:
                logger.info(f"Duplicate reminder prevented: {notification_key}")
                return False
            
            # Send with retry
            for attempt in range(3):
                try:
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode='HTML'
                    )
                    
                    notification_history[notification_key] = datetime.now()
                    logger.info(f"Daily reminder sent successfully: {notification_key}")
                    self._cleanup_notification_history()
                    return True
                    
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    if attempt < 2:
                        await asyncio.sleep(2 ** attempt)
            
            logger.error(f"Failed to send daily reminder after 3 attempts: {notification_key}")
            return False
            
        except Exception as e:
            logger.error(f"Error in send_daily_reminder: {e}")
            return False
    
    def remove_notification(self, user_id: int, notification_type: str):
        """Remove a scheduled notification for a user"""
        try:
            job_id = f"{notification_type}_{user_id}"
            job = self.scheduler.get_job(job_id)
            
            if job:
                self.scheduler.remove_job(job_id)
                logger.info(f"Removed notification: {job_id}")
                return True
            else:
                logger.info(f"No notification found to remove: {job_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to remove notification: {e}")
            return False
    
    def get_scheduled_notifications(self, user_id: int) -> list:
        """Get all scheduled notifications for a user"""
        try:
            jobs = []
            for job in self.scheduler.get_jobs():
                if str(user_id) in job.id:
                    jobs.append({
                        'id': job.id,
                        'next_run': job.next_run_time,
                        'trigger': str(job.trigger)
                    })
            return jobs
        except Exception as e:
            logger.error(f"Failed to get scheduled notifications: {e}")
            return []


# Global notification system instance
notification_system = NotificationSystem()

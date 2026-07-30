"""
Structured logging system for Rafeeq Islamic Telegram Super App.
Provides separate log files for different components.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional
from config.settings import settings


class LoggerSetup:
    """Centralized logging configuration"""
    
    @staticmethod
    def setup_logger(
        name: str,
        log_file: str,
        level: str = None,
        format_string: str = None
    ) -> logging.Logger:
        """
        Setup a logger with file and console handlers.
        
        Args:
            name: Logger name
            log_file: Log file path
            level: Logging level (default from settings)
            format_string: Log format string (default from settings)
        
        Returns:
            Configured logger instance
        """
        if level is None:
            level = settings.LOG_LEVEL
        if format_string is None:
            format_string = settings.LOG_FORMAT
        
        # Create logger
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        
        # Avoid duplicate handlers
        if logger.handlers:
            return logger
        
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # File handler with rotation
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=settings.LOG_MAX_BYTES,
            backupCount=settings.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(logging.Formatter(format_string))
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, level.upper()))
        console_handler.setFormatter(logging.Formatter(format_string))
        
        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    @staticmethod
    def setup_all_loggers() -> None:
        """Setup all application loggers"""
        # Main application logger
        LoggerSetup.setup_logger(
            "rafeeq",
            os.path.join(settings.LOG_DIR, "app.log")
        )
        
        # Error logger
        LoggerSetup.setup_logger(
            "rafeeq.error",
            os.path.join(settings.LOG_DIR, "error.log"),
            level="ERROR"
        )
        
        # API logger
        LoggerSetup.setup_logger(
            "rafeeq.api",
            os.path.join(settings.LOG_DIR, "api.log")
        )
        
        # Scheduler logger
        LoggerSetup.setup_logger(
            "rafeeq.scheduler",
            os.path.join(settings.LOG_DIR, "scheduler.log")
        )
        
        # Database logger
        LoggerSetup.setup_logger(
            "rafeeq.database",
            os.path.join(settings.LOG_DIR, "database.log")
        )
        
        # Cache logger
        LoggerSetup.setup_logger(
            "rafeeq.cache",
            os.path.join(settings.LOG_DIR, "cache.log")
        )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger by name.
    
    Args:
        name: Logger name (e.g., "rafeeq.api")
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Setup loggers on import
LoggerSetup.setup_all_loggers()

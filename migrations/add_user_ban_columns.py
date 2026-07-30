"""
Database migration script to add ban-related columns to users table.
Run this script to add: is_banned, ban_reason, banned_at columns.
"""

import asyncio
import asyncpg
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
load_dotenv(project_root / ".env")

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate():
    """Add missing columns to users table"""
    try:
        # Load settings from environment
        DATABASE_URL = os.getenv("DATABASE_URL")
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable not set")
        
        # Convert SQLAlchemy URL to asyncpg format
        # Replace postgresql+asyncpg:// with postgresql://
        if DATABASE_URL.startswith("postgresql+asyncpg://"):
            DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL)
        logger.info("Connected to database")
        
        # Check if columns exist
        check_is_banned = await conn.fetchval(
            "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'is_banned')"
        )
        check_ban_reason = await conn.fetchval(
            "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'ban_reason')"
        )
        check_banned_at = await conn.fetchval(
            "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'banned_at')"
        )
        
        # Add is_banned column if not exists
        if not check_is_banned:
            await conn.execute(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_banned BOOLEAN DEFAULT FALSE"
            )
            logger.info("Added is_banned column")
        else:
            logger.info("is_banned column already exists")
        
        # Add ban_reason column if not exists
        if not check_ban_reason:
            await conn.execute(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS ban_reason VARCHAR"
            )
            logger.info("Added ban_reason column")
        else:
            logger.info("ban_reason column already exists")
        
        # Add banned_at column if not exists
        if not check_banned_at:
            await conn.execute(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS banned_at TIMESTAMP"
            )
            logger.info("Added banned_at column")
        else:
            logger.info("banned_at column already exists")
        
        # Close connection
        await conn.close()
        logger.info("Migration completed successfully")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(migrate())

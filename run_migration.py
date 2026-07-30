"""
Run database migration to convert Telegram ID columns to BIGINT.
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def run_migration():
    """Execute the migration SQL"""
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    migration_sql = """
    -- Drop foreign key constraints that reference users.id
    ALTER TABLE module_usage DROP CONSTRAINT IF EXISTS module_usage_user_id_fkey;
    ALTER TABLE user_achievements DROP CONSTRAINT IF EXISTS user_achievements_user_id_fkey;

    -- Convert users.id to BIGINT (primary key)
    ALTER TABLE users ALTER COLUMN id TYPE BIGINT;

    -- Convert user_metrics.id to BIGINT (primary key)
    ALTER TABLE user_metrics ALTER COLUMN id TYPE BIGINT;

    -- Convert foreign key columns to BIGINT
    ALTER TABLE module_usage ALTER COLUMN user_id TYPE BIGINT;
    ALTER TABLE user_achievements ALTER COLUMN user_id TYPE BIGINT;

    -- Convert user_activity_logs.user_id to BIGINT
    ALTER TABLE user_activity_logs ALTER COLUMN user_id TYPE BIGINT;

    -- Recreate foreign key constraints with BIGINT
    ALTER TABLE module_usage ADD CONSTRAINT module_usage_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

    ALTER TABLE user_achievements ADD CONSTRAINT user_achievements_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
    """
    
    try:
        async with engine.begin() as conn:
            print("Starting migration: Converting Telegram ID columns to BIGINT...")
            
            # Execute migration in a transaction
            await conn.execute(text("BEGIN"))
            
            try:
                # Drop constraints
                print("Dropping foreign key constraints...")
                await conn.execute(text("ALTER TABLE module_usage DROP CONSTRAINT IF EXISTS module_usage_user_id_fkey"))
                await conn.execute(text("ALTER TABLE user_achievements DROP CONSTRAINT IF EXISTS user_achievements_user_id_fkey"))
                
                # Convert columns
                print("Converting users.id to BIGINT...")
                await conn.execute(text("ALTER TABLE users ALTER COLUMN id TYPE BIGINT"))
                
                print("Converting user_metrics.id to BIGINT...")
                await conn.execute(text("ALTER TABLE user_metrics ALTER COLUMN id TYPE BIGINT"))
                
                print("Converting module_usage.user_id to BIGINT...")
                await conn.execute(text("ALTER TABLE module_usage ALTER COLUMN user_id TYPE BIGINT"))
                
                print("Converting user_achievements.user_id to BIGINT...")
                await conn.execute(text("ALTER TABLE user_achievements ALTER COLUMN user_id TYPE BIGINT"))
                
                print("Converting user_activity_logs.user_id to BIGINT...")
                await conn.execute(text("ALTER TABLE user_activity_logs ALTER COLUMN user_id TYPE BIGINT"))
                
                # Recreate constraints
                print("Recreating foreign key constraints...")
                await conn.execute(text("""
                    ALTER TABLE module_usage ADD CONSTRAINT module_usage_user_id_fkey 
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                """))
                
                await conn.execute(text("""
                    ALTER TABLE user_achievements ADD CONSTRAINT user_achievements_user_id_fkey 
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                """))
                
                await conn.execute(text("COMMIT"))
                print("✅ Migration completed successfully!")
                
            except Exception as e:
                await conn.execute(text("ROLLBACK"))
                print(f"❌ Migration failed, rolled back: {e}")
                raise
                
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_migration())

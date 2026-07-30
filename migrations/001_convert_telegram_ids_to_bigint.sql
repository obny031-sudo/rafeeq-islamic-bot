-- Migration: Convert Telegram ID columns from INTEGER to BIGINT
-- Reason: Telegram IDs can exceed 32-bit signed integer limit (2,147,483,647)
-- Date: 2026-07-21

-- Start transaction
BEGIN;

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

-- Commit transaction
COMMIT;

-- Verification queries (run these after migration to verify)
-- SELECT column_name, data_type FROM information_schema.columns 
-- WHERE table_name IN ('users', 'user_metrics', 'module_usage', 'user_achievements', 'user_activity_logs')
-- AND column_name IN ('id', 'user_id');

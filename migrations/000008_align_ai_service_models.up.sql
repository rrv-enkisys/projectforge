-- Migration 008: Align database schema with AI service SQLAlchemy models
-- This migration updates the documents and chat_sessions tables to match
-- the field names and types expected by the AI service models.

-- ===== Documents table alignment =====

-- Add file_path (model uses this instead of gcs_path)
ALTER TABLE documents ADD COLUMN IF NOT EXISTS file_path TEXT;
UPDATE documents SET file_path = gcs_path WHERE file_path IS NULL;

-- Add status as VARCHAR (model uses text, not the processing_status enum)
ALTER TABLE documents ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'pending';
UPDATE documents SET status = processing_status::TEXT;

-- Add error_message
ALTER TABLE documents ADD COLUMN IF NOT EXISTS error_message TEXT;

-- Remove old columns (after data copied)
ALTER TABLE documents DROP COLUMN IF EXISTS gcs_path;
ALTER TABLE documents DROP COLUMN IF EXISTS processing_status;

-- ===== Chat sessions table alignment =====

-- Add title column
ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS title VARCHAR(255);

-- Change user_id from UUID FK to VARCHAR(255) for Firebase UIDs
-- Step 1: drop existing FK constraint and index
ALTER TABLE chat_sessions DROP CONSTRAINT IF EXISTS chat_sessions_user_id_fkey;
DROP INDEX IF EXISTS idx_chat_sessions_user_id;

-- Step 2: rename old column, add new, copy data, drop old
ALTER TABLE chat_sessions ADD COLUMN user_id_new VARCHAR(255);
UPDATE chat_sessions SET user_id_new = user_id::TEXT;
ALTER TABLE chat_sessions DROP COLUMN user_id;
ALTER TABLE chat_sessions RENAME COLUMN user_id_new TO user_id;
ALTER TABLE chat_sessions ALTER COLUMN user_id SET NOT NULL;

-- Step 3: recreate index
CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);

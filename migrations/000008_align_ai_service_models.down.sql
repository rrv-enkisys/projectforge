-- Rollback migration 008: Restore original schema

-- ===== Documents table rollback =====
ALTER TABLE documents ADD COLUMN IF NOT EXISTS gcs_path TEXT;
UPDATE documents SET gcs_path = file_path WHERE gcs_path IS NULL;

ALTER TABLE documents ADD COLUMN IF NOT EXISTS processing_status processing_status DEFAULT 'pending';
UPDATE documents SET processing_status = status::processing_status;

ALTER TABLE documents DROP COLUMN IF EXISTS file_path;
ALTER TABLE documents DROP COLUMN IF EXISTS status;
ALTER TABLE documents DROP COLUMN IF EXISTS error_message;

-- ===== Chat sessions rollback =====
ALTER TABLE chat_sessions DROP COLUMN IF EXISTS title;

-- Restore user_id as UUID FK (best effort - may fail if data isn't valid UUIDs)
ALTER TABLE chat_sessions ADD COLUMN user_id_old UUID;
-- Skip data copy as Firebase UIDs are not valid UUIDs
ALTER TABLE chat_sessions DROP COLUMN user_id;
ALTER TABLE chat_sessions RENAME COLUMN user_id_old TO user_id;
DROP INDEX IF EXISTS idx_chat_sessions_user_id;

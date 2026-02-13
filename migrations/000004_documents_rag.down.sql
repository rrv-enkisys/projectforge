-- Disable RLS and drop policies
DROP POLICY IF EXISTS tenant_isolation_chat_messages ON chat_messages;
ALTER TABLE chat_messages DISABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation_chat_sessions ON chat_sessions;
ALTER TABLE chat_sessions DISABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation_document_chunks ON document_chunks;
ALTER TABLE document_chunks DISABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation_documents ON documents;
ALTER TABLE documents DISABLE ROW LEVEL SECURITY;

-- Drop tables in reverse order
DROP TABLE IF EXISTS chat_messages;
DROP TABLE IF EXISTS chat_sessions;
DROP TABLE IF EXISTS document_chunks;
DROP TABLE IF EXISTS documents;

-- Drop vector extension (optional, comment out if you want to keep it)
-- DROP EXTENSION IF EXISTS vector;

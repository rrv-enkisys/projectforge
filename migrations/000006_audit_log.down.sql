-- Drop audit trigger function
DROP FUNCTION IF EXISTS log_audit_change();

-- Disable RLS and drop policy
DROP POLICY IF EXISTS tenant_isolation_audit_log ON audit_log;
ALTER TABLE audit_log DISABLE ROW LEVEL SECURITY;

-- Drop audit log table
DROP TABLE IF EXISTS audit_log;

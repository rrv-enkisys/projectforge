-- Disable RLS and drop policies
DROP POLICY IF EXISTS tenant_isolation_notification_preferences ON notification_preferences;
ALTER TABLE notification_preferences DISABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation_notification_log ON notification_log;
ALTER TABLE notification_log DISABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation_email_templates ON email_templates;
ALTER TABLE email_templates DISABLE ROW LEVEL SECURITY;

-- Drop tables in reverse order
DROP TABLE IF EXISTS notification_preferences;
DROP TABLE IF EXISTS notification_log;
DROP TABLE IF EXISTS email_templates;

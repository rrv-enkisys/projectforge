-- Drop tables in reverse order
DROP TABLE IF EXISTS clients;
DROP TABLE IF EXISTS organization_members;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS organizations;

-- Drop function
DROP FUNCTION IF EXISTS update_updated_at_column();

-- Drop ENUMs
DROP TYPE IF EXISTS chat_role;
DROP TYPE IF EXISTS notification_status;
DROP TYPE IF EXISTS trigger_type;
DROP TYPE IF EXISTS processing_status;
DROP TYPE IF EXISTS dependency_type;
DROP TYPE IF EXISTS assignment_role;
DROP TYPE IF EXISTS task_priority;
DROP TYPE IF EXISTS task_status;
DROP TYPE IF EXISTS project_status;
DROP TYPE IF EXISTS org_role;

-- Drop extensions (optional, comment out if you want to keep them)
-- DROP EXTENSION IF EXISTS "pgcrypto";
-- DROP EXTENSION IF EXISTS "uuid-ossp";

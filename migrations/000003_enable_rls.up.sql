-- Enable Row Level Security on all multi-tenant tables

-- Clients
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_clients ON clients
    USING (organization_id = current_setting('app.current_organization_id')::uuid);

-- Projects
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_projects ON projects
    USING (organization_id = current_setting('app.current_organization_id')::uuid);

-- Milestones
ALTER TABLE milestones ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_milestones ON milestones
    USING (organization_id = current_setting('app.current_organization_id')::uuid);

-- Tasks
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_tasks ON tasks
    USING (organization_id = current_setting('app.current_organization_id')::uuid);

-- Task Dependencies
ALTER TABLE task_dependencies ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_task_dependencies ON task_dependencies
    USING (organization_id = current_setting('app.current_organization_id')::uuid);

-- Task Assignments
ALTER TABLE task_assignments ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_task_assignments ON task_assignments
    USING (organization_id = current_setting('app.current_organization_id')::uuid);

-- Task Comments
ALTER TABLE task_comments ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_task_comments ON task_comments
    USING (organization_id = current_setting('app.current_organization_id')::uuid);

-- Note: organization_members doesn't need RLS as it's already filtered by organization_id in queries
-- Users table is global and doesn't need RLS
-- Organizations table is accessed by authenticated users based on their membership

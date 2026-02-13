-- Disable Row Level Security and drop policies

-- Task Comments
DROP POLICY IF EXISTS tenant_isolation_task_comments ON task_comments;
ALTER TABLE task_comments DISABLE ROW LEVEL SECURITY;

-- Task Assignments
DROP POLICY IF EXISTS tenant_isolation_task_assignments ON task_assignments;
ALTER TABLE task_assignments DISABLE ROW LEVEL SECURITY;

-- Task Dependencies
DROP POLICY IF EXISTS tenant_isolation_task_dependencies ON task_dependencies;
ALTER TABLE task_dependencies DISABLE ROW LEVEL SECURITY;

-- Tasks
DROP POLICY IF EXISTS tenant_isolation_tasks ON tasks;
ALTER TABLE tasks DISABLE ROW LEVEL SECURITY;

-- Milestones
DROP POLICY IF EXISTS tenant_isolation_milestones ON milestones;
ALTER TABLE milestones DISABLE ROW LEVEL SECURITY;

-- Projects
DROP POLICY IF EXISTS tenant_isolation_projects ON projects;
ALTER TABLE projects DISABLE ROW LEVEL SECURITY;

-- Clients
DROP POLICY IF EXISTS tenant_isolation_clients ON clients;
ALTER TABLE clients DISABLE ROW LEVEL SECURITY;

# Database Migrations

This directory contains SQL migrations for ProjectForge PostgreSQL database.

## Migration Files

Migrations are numbered sequentially and include both "up" (apply) and "down" (rollback) scripts:

### 000001 - Initial Schema
- Extensions: uuid-ossp, pgcrypto
- ENUMs: All status and role types
- Tables: organizations, users, organization_members, clients
- Trigger: update_updated_at_column()

### 000002 - Projects and Tasks
- Tables: projects, milestones, tasks
- Related: task_dependencies, task_assignments, task_comments
- Indexes: Optimized for common queries

### 000003 - Row Level Security (RLS)
- Enables RLS on all multi-tenant tables
- Creates tenant_isolation policies
- Uses: current_setting('app.current_organization_id')::uuid

### 000004 - Documents and RAG
- Extension: pgvector
- Tables: documents, document_chunks (with vector embeddings)
- Tables: chat_sessions, chat_messages
- Vector index: ivfflat for cosine similarity

### 000005 - Notifications
- Tables: email_templates, notification_log, notification_preferences
- Supports: Email, Slack, Teams notifications

### 000006 - Audit Log
- Table: audit_log with JSONB changes
- Function: log_audit_change() for automatic logging
- GIN index for JSONB queries

## Running Migrations

### Using golang-migrate

```bash
# Install golang-migrate
brew install golang-migrate  # macOS
# or
go install -tags 'postgres' github.com/golang-migrate/migrate/v4/cmd/migrate@latest

# Run all migrations
migrate -path migrations -database "postgresql://user:pass@localhost:5432/projectforge?sslmode=disable" up

# Rollback last migration
migrate -path migrations -database "postgresql://user:pass@localhost:5432/projectforge?sslmode=disable" down 1

# Check migration version
migrate -path migrations -database "postgresql://user:pass@localhost:5432/projectforge?sslmode=disable" version
```

### Using psql (manual)

```bash
# Apply migration
psql -U postgres -d projectforge -f migrations/000001_initial_schema.up.sql

# Rollback migration
psql -U postgres -d projectforge -f migrations/000001_initial_schema.down.sql
```

### Using Docker

```bash
# Apply all migrations
docker run --rm \
  -v $(pwd)/migrations:/migrations \
  --network projectforge-network \
  migrate/migrate \
  -path=/migrations \
  -database "postgresql://postgres:postgres@postgres:5432/projectforge?sslmode=disable" \
  up

# Rollback all migrations
docker run --rm \
  -v $(pwd)/migrations:/migrations \
  --network projectforge-network \
  migrate/migrate \
  -path=/migrations \
  -database "postgresql://postgres:postgres@postgres:5432/projectforge?sslmode=disable" \
  down -all
```

## Testing Migrations

### Local Development

```bash
# Start PostgreSQL with Docker
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
sleep 5

# Run migrations
migrate -path migrations -database "postgresql://postgres:postgres@localhost:5432/projectforge?sslmode=disable" up

# Verify tables
psql -U postgres -d projectforge -c "\dt"

# Verify RLS policies
psql -U postgres -d projectforge -c "SELECT schemaname, tablename, policyname FROM pg_policies;"
```

### Testing RLS

```sql
-- Set organization context
SET app.current_organization_id = 'org-uuid-here';

-- Query should only return data for this organization
SELECT * FROM projects;

-- Reset context
RESET app.current_organization_id;
```

### Testing Vector Search

```sql
-- Insert test embedding
INSERT INTO document_chunks (organization_id, document_id, content, embedding, chunk_index)
VALUES (
    'org-uuid',
    'doc-uuid',
    'Test content',
    '[0.1, 0.2, ...]'::vector(768),
    0
);

-- Test similarity search
SELECT content, 1 - (embedding <=> '[0.1, 0.2, ...]'::vector(768)) as similarity
FROM document_chunks
WHERE organization_id = 'org-uuid'
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector(768)
LIMIT 5;
```

## Schema Conventions

All tables follow these conventions:

- **Primary Key**: `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`
- **Timestamps**: `created_at` and `updated_at` (with trigger)
- **Multi-tenant**: `organization_id UUID NOT NULL REFERENCES organizations(id)`
- **Naming**: snake_case for tables and columns
- **Foreign Keys**: Proper ON DELETE CASCADE or SET NULL

## Notes

1. **Always test migrations** in development before applying to production
2. **Backup database** before running migrations in production
3. **RLS policies** require setting `app.current_organization_id` session variable
4. **Vector embeddings** are 768 dimensions for Vertex AI textembedding-gecko@004
5. **Audit logging** is optional - uncomment triggers in 000006 to enable

## Troubleshooting

### Migration fails with "relation already exists"
```bash
# Check current version
migrate -database $DATABASE_URL version

# Force version (use carefully)
migrate -database $DATABASE_URL force VERSION
```

### RLS blocking queries
```sql
-- Disable RLS for superuser (development only)
ALTER TABLE projects DISABLE ROW LEVEL SECURITY;

-- Or set organization context
SET app.current_organization_id = 'your-org-uuid';
```

### Vector index performance
```sql
-- Adjust lists parameter based on data size
DROP INDEX idx_document_chunks_embedding;
CREATE INDEX idx_document_chunks_embedding ON document_chunks
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 200);  -- Adjust based on row count
```

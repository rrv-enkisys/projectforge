# ProjectForge - AI-Powered Project Management Platform

## Project Overview

ProjectForge is a multi-tenant SaaS platform for project management with AI capabilities, designed to compete with enterprise solutions like Microsoft Project. The platform enables organizations to manage clients, projects, tasks, and milestones with intelligent features including RAG-based document Q&A and an AI project copilot.

## Architecture Summary

```
Frontend (React) → Cloud Load Balancer → API Gateway (Go/Cloud Run)
                                              ↓
                    ┌─────────────────────────┼─────────────────────────┐
                    ↓                         ↓                         ↓
             Core Service            AI Service              Notification Service
             (Python)                (Python)                      (Go)
                    ↓                         ↓                         ↓
                    └─────────────────────────┼─────────────────────────┘
                                              ↓
                         ┌────────────────────┼────────────────────┐
                         ↓                    ↓                    ↓
                    Cloud SQL           Cloud Storage         Firestore
                    (PostgreSQL)        (Documents)           (Realtime)
```

## Technology Stack

### Frontend
- **Framework**: React 18+ with TypeScript
- **Styling**: TailwindCSS + shadcn/ui
- **State**: Zustand + TanStack Query
- **Gantt**: frappe-gantt or DHTMLX Gantt
- **Kanban**: @dnd-kit/core
- **Build**: Vite

### Backend
- **API Gateway**: Go 1.22+ on Cloud Run
- **Core Service**: Python 3.12+ (FastAPI) on Cloud Run
- **AI Service**: Python 3.12+ (FastAPI) on Cloud Run
- **Notification Service**: Go 1.22+ on Cloud Run

### Data & AI
- **Database**: Cloud SQL (PostgreSQL 15+ with pgvector)
- **Realtime**: Firestore (sync state only)
- **Storage**: Cloud Storage
- **Auth**: Firebase Auth
- **Embeddings**: Vertex AI (textembedding-gecko@004)
- **LLM**: Vertex AI (Gemini 1.5 Pro)
- **Doc Processing**: Document AI

### Infrastructure
- **IaC**: Terraform
- **CI/CD**: Cloud Build
- **Monitoring**: Cloud Monitoring + Logging
- **Secrets**: Secret Manager

## Code Standards

### Python (Core & AI Services)
```bash
# Formatting and linting
black .
isort .
mypy --strict .
ruff check .

# Testing
pytest --cov=src tests/
```

**Patterns:**
- FastAPI for HTTP layer
- Pydantic v2 for validation
- SQLAlchemy 2.0 with async
- Repository pattern for data access
- Dependency injection via FastAPI Depends

**Example structure:**
```python
# src/tasks/router.py
from fastapi import APIRouter, Depends
from .service import TaskService
from .schemas import TaskCreate, TaskResponse

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/", response_model=TaskResponse)
async def create_task(
    data: TaskCreate,
    service: TaskService = Depends()
):
    return await service.create(data)
```

### Go (Gateway & Notifications)
```bash
# Formatting and linting
gofmt -w .
golangci-lint run

# Testing
go test -v -cover ./...
```

**Patterns:**
- Chi router for HTTP
- sqlx for database
- Wire for dependency injection
- Structured logging with slog
- Context propagation for tracing

**Example structure:**
```go
// internal/handler/task.go
func (h *TaskHandler) Create(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()
    orgID := middleware.GetOrgID(ctx)

    var req CreateTaskRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        h.respondError(w, err, http.StatusBadRequest)
        return
    }

    task, err := h.service.Create(ctx, orgID, req)
    if err != nil {
        h.respondError(w, err, http.StatusInternalServerError)
        return
    }

    h.respondJSON(w, task, http.StatusCreated)
}
```

### React (Frontend)
```bash
# Formatting and linting
eslint . --fix
prettier --write .

# Testing
vitest
playwright test
```

**Patterns:**
- Functional components only
- Custom hooks for logic extraction
- TanStack Query for server state
- Zustand for client state
- shadcn/ui for components

**Example structure:**
```tsx
// src/features/tasks/components/TaskCard.tsx
import { Card } from '@/components/ui/card';
import { useTask } from '../hooks/useTask';
import type { Task } from '../types';

interface TaskCardProps {
  taskId: string;
}

export function TaskCard({ taskId }: TaskCardProps) {
  const { task, isLoading } = useTask(taskId);

  if (isLoading) return <TaskCardSkeleton />;

  return (
    <Card className="p-4">
      <h3 className="font-semibold">{task.title}</h3>
      <p className="text-muted-foreground">{task.description}</p>
    </Card>
  );
}
```

## Multi-Tenancy

All database operations MUST respect tenant isolation:

```python
# Always include organization_id in queries
async def get_projects(self, org_id: UUID) -> list[Project]:
    return await self.db.execute(
        select(Project).where(Project.organization_id == org_id)
    )
```

```sql
-- RLS policies are enabled on all tables
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON projects
    USING (organization_id = current_setting('app.current_organization_id')::uuid);
```

## API Design Principles

1. **RESTful conventions**: Use proper HTTP methods and status codes
2. **Versioned endpoints**: All routes under `/api/v1/`
3. **Consistent responses**: Always return JSON with standard envelope
4. **Pagination**: Use cursor-based pagination for lists
5. **Error handling**: Return structured error objects

```json
// Success response
{
  "data": { ... },
  "meta": {
    "cursor": "next_page_token"
  }
}

// Error response
{
  "error": {
    "code": "TASK_NOT_FOUND",
    "message": "Task with ID xyz not found",
    "details": { ... }
  }
}
```

## RAG Implementation

Document processing pipeline:
1. Upload to Cloud Storage
2. Pub/Sub triggers processing job
3. Document AI extracts text
4. Text chunked (512 tokens, 50 overlap)
5. Vertex AI generates embeddings
6. Store chunks + vectors in pgvector

Query flow:
1. Embed user query
2. Vector similarity search (cosine distance)
3. Retrieve top 5 chunks
4. Augment prompt with context
5. Generate response with Gemini

```sql
-- Vector similarity search
SELECT content, 1 - (embedding <=> $1) as similarity
FROM document_chunks
WHERE document_id IN (SELECT id FROM documents WHERE project_id = $2)
ORDER BY embedding <=> $1
LIMIT 5;
```

## Testing Requirements

- **Unit tests**: All business logic
- **Integration tests**: API endpoints with test database
- **E2E tests**: Critical user flows with Playwright
- **Coverage**: Minimum 80% for core services

```bash
# Run all tests
turbo test

# Run specific service tests
turbo test --filter=core-service
```

## Environment Variables

Required secrets (stored in Secret Manager):
- `DATABASE_URL`: Cloud SQL connection string
- `FIREBASE_PROJECT_ID`: Firebase project
- `FIREBASE_PRIVATE_KEY`: Service account key
- `RESEND_API_KEY`: Email service
- `VERTEX_AI_PROJECT`: GCP project for AI
- `SLACK_BOT_TOKEN`: Slack integration
- `TEAMS_APP_ID`: Teams integration

## Common Commands

```bash
# Development
turbo dev                          # Start all services
turbo dev --filter=web             # Start frontend only
turbo dev --filter=core-service    # Start core service only

# Database
npm run db:migrate                 # Run migrations
npm run db:seed                    # Seed test data
npm run db:reset                   # Reset and reseed

# Deployment
terraform -chdir=infrastructure/terraform/environments/dev apply
gcloud run deploy api-gateway --source=./apps/api-gateway

# Code generation
npm run generate:types             # Generate TS types from schema
npm run generate:api               # Generate API client
```

## Key Files

- `/ARCHITECTURE.md` - Full system architecture
- `/apps/web/` - React frontend
- `/apps/api-gateway/` - Go API gateway
- `/apps/core-service/` - Python core service
- `/apps/ai-service/` - Python AI service
- `/apps/notification-service/` - Go notification service
- `/packages/shared-types/` - Shared TypeScript types
- `/packages/ui-components/` - Shared React components
- `/infrastructure/terraform/` - IaC definitions
- `/migrations/` - Database migrations

## Current Sprint Focus

[Update this section with current sprint goals]

- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

## Notes for Claude

1. **Always check tenant context** before any database operation
2. **Use structured logging** with request IDs for tracing
3. **Validate all inputs** at API boundaries
4. **Handle errors gracefully** with appropriate status codes
5. **Write tests** for new functionality
6. **Update migrations** when changing schema
7. **Use feature flags** for experimental features
8. **Document API changes** in OpenAPI specs

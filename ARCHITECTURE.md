# ProjectForge - Technical Architecture Document

**Version:** 1.0
**Date:** February 2025
**Status:** Approved for Development

---

## Executive Summary

ProjectForge is a multi-tenant, AI-powered project management platform designed to compete with enterprise solutions like Microsoft Project. The platform leverages Google Cloud Platform services for infrastructure, Firebase for authentication and real-time sync, and Vertex AI for intelligent features including RAG-based document Q&A and an AI project copilot.

---

## Technology Stack

### Frontend
| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | React 18+ with TypeScript | Core UI framework |
| Styling | TailwindCSS + shadcn/ui | Design system and components |
| State Management | Zustand + TanStack Query | Client state + server state |
| Gantt Chart | frappe-gantt or DHTMLX Gantt | Project timeline visualization |
| Kanban Board | @dnd-kit/core | Drag-and-drop task management |
| Real-time | Firebase SDK | Live updates |
| Build Tool | Vite | Fast development and builds |

### Backend Services

| Service | Language | Runtime | Responsibility |
|---------|----------|---------|----------------|
| API Gateway | Go 1.22+ | Cloud Run | Auth validation, routing, rate limiting |
| Core Service | Python 3.12+ | Cloud Run | Projects, tasks, users, milestones |
| AI Service | Python 3.12+ | Cloud Run | RAG, embeddings, AI copilot |
| Notification Service | Go 1.22+ | Cloud Run | Emails, Slack/Teams, webhooks |

### Data Layer

| Component | Service | Purpose |
|-----------|---------|---------|
| Primary Database | Cloud SQL (PostgreSQL 15+) | All application data, pgvector for embeddings |
| Real-time Sync | Firestore | Live Gantt/Kanban updates only |
| Object Storage | Cloud Storage | Documents, uploads, exports |
| Vector Search | pgvector extension | Document chunk embeddings |
| Task Queue | Cloud Tasks | Scheduled emails, async jobs |
| Event Bus | Cloud Pub/Sub | Event-driven architecture |

### AI & ML

| Component | Service | Purpose |
|-----------|---------|---------|
| Document Processing | Document AI | PDF parsing, OCR, table extraction |
| Embeddings | Vertex AI (textembedding-gecko@004) | 768-dim vectors for RAG |
| LLM | Vertex AI (Gemini 1.5 Pro) | RAG responses, AI Copilot |
| Vector Storage | pgvector in Cloud SQL | Similarity search |

### Infrastructure

| Component | Service | Purpose |
|-----------|---------|---------|
| Container Registry | Artifact Registry | Docker images |
| Secrets | Secret Manager | API keys, credentials |
| Monitoring | Cloud Monitoring + Logging | Observability |
| CDN | Cloud CDN | Static assets |
| Load Balancing | Cloud Load Balancer | SSL, routing |
| IaC | Terraform | Infrastructure as code |

### External Services

| Service | Provider | Purpose |
|---------|----------|---------|
| Transactional Email | Resend | Notifications, templates |
| Slack Integration | Slack API + MCP | Bot commands, notifications |
| Teams Integration | Microsoft Graph API | Bot commands, notifications |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Web App   │  │ Mobile PWA  │  │  Slack Bot  │  │ Teams Bot   │        │
│  │   (React)   │  │   (React)   │  │    (MCP)    │  │   (Graph)   │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
└─────────┼────────────────┼────────────────┼────────────────┼────────────────┘
          │                │                │                │
          └────────────────┴────────────────┴────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CLOUD LOAD BALANCER                                  │
│                    SSL Termination + Cloud CDN                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
┌─────────────────────────────────┐   ┌─────────────────────────────────┐
│         STATIC ASSETS           │   │         API GATEWAY             │
│      Cloud Storage + CDN        │   │          Cloud Run              │
│                                 │   │            (Go)                 │
│  • React bundle                 │   │                                 │
│  • Images, fonts                │   │  • JWT validation (Firebase)    │
│  • PWA manifest                 │   │  • Tenant resolution            │
└─────────────────────────────────┘   │  • Rate limiting                │
                                      │  • Request routing              │
                                      │  • Request/Response logging     │
                                      └─────────────────────────────────┘
                                                      │
                    ┌─────────────────────────────────┼─────────────────────────────────┐
                    │                                 │                                 │
                    ▼                                 ▼                                 ▼
┌─────────────────────────────┐   ┌─────────────────────────────┐   ┌─────────────────────────────┐
│       CORE SERVICE          │   │        AI SERVICE           │   │   NOTIFICATION SERVICE      │
│        Cloud Run            │   │        Cloud Run            │   │        Cloud Run            │
│        (Python)             │   │        (Python)             │   │          (Go)               │
│                             │   │                             │   │                             │
│  • Organizations CRUD       │   │  • Document ingestion       │   │  • Email sending (Resend)   │
│  • Clients CRUD             │   │  • Embedding generation     │   │  • Slack integration        │
│  • Projects CRUD            │   │  • RAG query processing     │   │  • Teams integration        │
│  • Tasks & Dependencies     │   │  • AI Copilot logic         │   │  • Webhook delivery         │
│  • Milestones               │   │  • Smart suggestions        │   │  • Template rendering       │
│  • Users & Assignments      │   │                             │   │                             │
│  • Audit logging            │   │                             │   │                             │
└─────────────────────────────┘   └─────────────────────────────┘   └─────────────────────────────┘
          │                                 │                                 │
          │                       ┌─────────┴─────────┐                       │
          │                       ▼                   ▼                       │
          │           ┌─────────────────┐   ┌─────────────────┐               │
          │           │   Document AI   │   │   Vertex AI     │               │
          │           │                 │   │                 │               │
          │           │  • PDF parsing  │   │  • Embeddings   │               │
          │           │  • OCR          │   │  • Gemini 1.5   │               │
          │           │  • Tables       │   │                 │               │
          │           └─────────────────┘   └─────────────────┘               │
          │                                                                   │
          └───────────────────────────────┬───────────────────────────────────┘
                                          │
          ┌───────────────────────────────┼───────────────────────────────┐
          │                               │                               │
          ▼                               ▼                               ▼
┌─────────────────────┐       ┌─────────────────────┐       ┌─────────────────────┐
│     CLOUD SQL       │       │    CLOUD STORAGE    │       │      FIRESTORE      │
│   (PostgreSQL 15)   │       │                     │       │   (Real-time only)  │
│                     │       │  • /documents/      │       │                     │
│  • All app data     │       │  • /exports/        │       │  • Task positions   │
│  • pgvector ext     │       │  • /templates/      │       │  • Gantt updates    │
│  • Multi-tenant RLS │       │  • /avatars/        │       │  • Kanban state     │
└─────────────────────┘       └─────────────────────┘       └─────────────────────┘
          │
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ASYNC PROCESSING                                  │
│  ┌─────────────────────┐              ┌─────────────────────┐              │
│  │     Cloud Pub/Sub   │              │    Cloud Tasks      │              │
│  │                     │              │                     │              │
│  │  Topics:            │              │  Queues:            │              │
│  │  • document-new     │              │  • email-send       │              │
│  │  • task-updated     │              │  • document-process │              │
│  │  • milestone-done   │              │  • report-generate  │              │
│  │  • notification-req │              │  • webhook-deliver  │              │
│  └─────────────────────┘              └─────────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Model

### Entity Relationship Diagram

```
┌─────────────────────┐       ┌─────────────────────┐
│   organizations     │       │       users         │
├─────────────────────┤       ├─────────────────────┤
│ id (PK)             │       │ id (PK)             │
│ name                │       │ firebase_uid        │
│ slug (unique)       │       │ email               │
│ settings (JSONB)    │       │ name                │
│ branding (JSONB)    │       │ avatar_url          │
│ created_at          │       │ contact_info (JSONB)│
│ updated_at          │       │ created_at          │
└─────────┬───────────┘       └──────────┬──────────┘
          │                              │
          │    ┌─────────────────────┐   │
          │    │ organization_members│   │
          │    ├─────────────────────┤   │
          └───►│ organization_id (FK)│◄──┘
               │ user_id (FK)        │
               │ role (enum)         │
               │ invited_at          │
               │ joined_at           │
               └─────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          ▼                             │
┌─────────────────────┐                 │
│      clients        │                 │
├─────────────────────┤                 │
│ id (PK)             │                 │
│ organization_id (FK)│                 │
│ name                │                 │
│ contact_info (JSONB)│                 │
│ settings (JSONB)    │                 │
│ created_at          │                 │
└─────────┬───────────┘                 │
          │                             │
          ▼                             │
┌─────────────────────┐                 │
│     projects        │                 │
├─────────────────────┤                 │
│ id (PK)             │                 │
│ client_id (FK)      │                 │
│ name                │                 │
│ description         │                 │
│ status (enum)       │                 │
│ start_date          │                 │
│ end_date            │                 │
│ settings (JSONB)    │                 │
│ created_at          │                 │
└─────────┬───────────┘                 │
          │                             │
          ├──────────────────────────┐  │
          │                          │  │
          ▼                          ▼  │
┌─────────────────────┐    ┌─────────────────────┐
│    milestones       │    │       tasks         │
├─────────────────────┤    ├─────────────────────┤
│ id (PK)             │    │ id (PK)             │
│ project_id (FK)     │    │ project_id (FK)     │
│ name                │    │ milestone_id (FK)   │
│ description         │    │ parent_task_id (FK) │
│ target_date         │    │ title               │
│ status (enum)       │    │ description         │
│ created_at          │    │ status (enum)       │
└─────────────────────┘    │ priority (enum)     │
                           │ start_date          │
                           │ due_date            │
                           │ estimated_hours     │
                           │ actual_hours        │
                           │ position (int)      │
                           │ created_at          │
                           └─────────┬───────────┘
                                     │
          ┌──────────────────────────┼──────────────────────────┐
          │                          │                          │
          ▼                          ▼                          ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│ task_dependencies   │    │  task_assignments   │    │   task_comments     │
├─────────────────────┤    ├─────────────────────┤    ├─────────────────────┤
│ task_id (FK)        │    │ task_id (FK)        │    │ id (PK)             │
│ depends_on_id (FK)  │    │ user_id (FK)        │◄───│ task_id (FK)        │
│ dependency_type     │    │ role (enum)         │    │ user_id (FK)        │
└─────────────────────┘    └─────────────────────┘    │ content             │
                                     ▲                │ created_at          │
                                     │                └─────────────────────┘
                                     │
┌─────────────────────────────────────────────────────────────────────────────┐
│                            DOCUMENTS & RAG                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┐         ┌─────────────────────┐                   │
│  │     documents       │         │   document_chunks   │                   │
│  ├─────────────────────┤         ├─────────────────────┤                   │
│  │ id (PK)             │────────►│ id (PK)             │                   │
│  │ project_id (FK)     │         │ document_id (FK)    │                   │
│  │ name                │         │ content             │                   │
│  │ gcs_path            │         │ embedding vector(768)│                  │
│  │ file_type           │         │ chunk_index         │                   │
│  │ file_size           │         │ metadata (JSONB)    │                   │
│  │ uploaded_by (FK)    │         │ created_at          │                   │
│  │ processing_status   │         └─────────────────────┘                   │
│  │ created_at          │                                                   │
│  └─────────────────────┘                                                   │
│                                                                             │
│  ┌─────────────────────┐         ┌─────────────────────┐                   │
│  │   chat_sessions     │         │   chat_messages     │                   │
│  ├─────────────────────┤         ├─────────────────────┤                   │
│  │ id (PK)             │────────►│ id (PK)             │                   │
│  │ project_id (FK)     │         │ session_id (FK)     │                   │
│  │ user_id (FK)        │         │ role (enum)         │                   │
│  │ created_at          │         │ content             │                   │
│  └─────────────────────┘         │ sources (JSONB)     │                   │
│                                  │ created_at          │                   │
│                                  └─────────────────────┘                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           NOTIFICATIONS                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┐         ┌─────────────────────┐                   │
│  │   email_templates   │         │  notification_log   │                   │
│  ├─────────────────────┤         ├─────────────────────┤                   │
│  │ id (PK)             │         │ id (PK)             │                   │
│  │ organization_id (FK)│         │ type (enum)         │                   │
│  │ client_id (FK) null │         │ recipient_id (FK)   │                   │
│  │ project_id (FK) null│         │ task_id (FK) null   │                   │
│  │ trigger_type (enum) │         │ project_id (FK) null│                   │
│  │ subject_template    │         │ template_id (FK)    │                   │
│  │ body_template       │         │ status (enum)       │                   │
│  │ is_active           │         │ sent_at             │                   │
│  │ created_at          │         │ metadata (JSONB)    │                   │
│  └─────────────────────┘         │ created_at          │                   │
│                                  └─────────────────────┘                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                             AUDIT                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐                                                    │
│  │    audit_log        │                                                    │
│  ├─────────────────────┤                                                    │
│  │ id (PK)             │                                                    │
│  │ organization_id (FK)│                                                    │
│  │ user_id (FK)        │                                                    │
│  │ action (enum)       │                                                    │
│  │ entity_type         │                                                    │
│  │ entity_id           │                                                    │
│  │ changes (JSONB)     │                                                    │
│  │ ip_address          │                                                    │
│  │ user_agent          │                                                    │
│  │ created_at          │                                                    │
│  └─────────────────────┘                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Enums

```sql
-- User roles within an organization
CREATE TYPE org_role AS ENUM ('admin', 'pm', 'collaborator', 'client');

-- Project status
CREATE TYPE project_status AS ENUM ('planning', 'active', 'on_hold', 'completed', 'archived');

-- Task status (for Kanban)
CREATE TYPE task_status AS ENUM ('backlog', 'todo', 'in_progress', 'review', 'done');

-- Task priority
CREATE TYPE task_priority AS ENUM ('low', 'medium', 'high', 'critical');

-- Task assignment role
CREATE TYPE assignment_role AS ENUM ('responsible', 'participant', 'reviewer');

-- Task dependency type
CREATE TYPE dependency_type AS ENUM ('finish_to_start', 'start_to_start', 'finish_to_finish', 'start_to_finish');

-- Document processing status
CREATE TYPE processing_status AS ENUM ('pending', 'processing', 'completed', 'failed');

-- Notification trigger types
CREATE TYPE trigger_type AS ENUM ('task_assigned', 'due_date_near', 'task_completed', 'task_overdue', 'milestone_reached');

-- Notification delivery status
CREATE TYPE notification_status AS ENUM ('pending', 'sent', 'delivered', 'failed', 'bounced');
```

---

## Multi-Tenancy Strategy

### Row Level Security (RLS)

All tables include `organization_id` and use PostgreSQL RLS policies:

```sql
-- Enable RLS
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

-- Policy for data isolation
CREATE POLICY tenant_isolation ON projects
    USING (organization_id = current_setting('app.current_organization_id')::uuid);

-- Set context in each request
SET app.current_organization_id = 'org-uuid-here';
```

### Tenant Resolution Flow

```
Request → API Gateway → Extract JWT → Validate Firebase Token
                                           ↓
                                    Extract org_id from claims
                                           ↓
                                    Set PostgreSQL session variable
                                           ↓
                                    All queries filtered by RLS
```

---

## Authentication Flow

### Firebase Auth Integration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AUTHENTICATION FLOW                                │
└─────────────────────────────────────────────────────────────────────────────┘

  User                    Frontend              Firebase             API Gateway
   │                         │                     │                      │
   │  1. Login/Signup        │                     │                      │
   │────────────────────────►│                     │                      │
   │                         │                     │                      │
   │                         │  2. Auth Request    │                      │
   │                         │────────────────────►│                      │
   │                         │                     │                      │
   │                         │  3. ID Token + Refresh Token               │
   │                         │◄────────────────────│                      │
   │                         │                     │                      │
   │  4. Store tokens        │                     │                      │
   │◄────────────────────────│                     │                      │
   │                         │                     │                      │
   │  5. API Request with Bearer Token             │                      │
   │──────────────────────────────────────────────────────────────────────►│
   │                         │                     │                      │
   │                         │                     │  6. Verify Token     │
   │                         │                     │◄─────────────────────│
   │                         │                     │                      │
   │                         │                     │  7. Token Valid +    │
   │                         │                     │     User Claims      │
   │                         │                     │─────────────────────►│
   │                         │                     │                      │
   │                         │                     │       8. Route to    │
   │                         │                     │          Service     │
   │◄──────────────────────────────────────────────────────────────────────│
```

### Custom Claims

Firebase custom claims store organization memberships:

```json
{
  "organizations": {
    "org-uuid-1": "admin",
    "org-uuid-2": "collaborator"
  },
  "default_organization": "org-uuid-1"
}
```

---

## Real-time Synchronization

### Firestore Structure (Sync Only)

```
/sync/{organizationId}/
  /projects/{projectId}/
    /tasks/{taskId}
      - position: number
      - status: string
      - updatedAt: timestamp
      - updatedBy: string
    /gantt_state
      - viewMode: string
      - scrollPosition: number
```

### Sync Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        REAL-TIME SYNC STRATEGY                              │
└─────────────────────────────────────────────────────────────────────────────┘

  Source of Truth: Cloud SQL
  Real-time Layer: Firestore (ephemeral sync state)

  Write Flow:
  ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
  │  Client  │────►│   API    │────►│Cloud SQL │────►│Firestore │
  │ (Kanban) │     │ Gateway  │     │ (persist)│     │  (sync)  │
  └──────────┘     └──────────┘     └──────────┘     └──────────┘
                                          │
                                          ▼
                                    Pub/Sub event
                                          │
                                          ▼
                                   Other clients
                                   receive update
                                   via Firestore
                                   listener

  Read Flow:
  - Initial load: Cloud SQL (complete data)
  - Live updates: Firestore listeners (position/status changes)
  - Reconciliation: Periodic Cloud SQL sync for consistency
```

---

## RAG Pipeline

### Document Processing Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DOCUMENT INGESTION PIPELINE                            │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌──────────┐         ┌──────────┐         ┌──────────┐
  │  Upload  │────────►│  Cloud   │────────►│ Pub/Sub  │
  │   API    │         │ Storage  │ trigger │doc-upload│
  └──────────┘         └──────────┘         └──────────┘
                                                  │
                                                  ▼
                                        ┌─────────────────┐
                                        │  Cloud Run Job  │
                                        │  (Processor)    │
                                        └────────┬────────┘
                                                 │
                    ┌────────────────────────────┼────────────────────────────┐
                    │                            │                            │
                    ▼                            ▼                            ▼
           ┌──────────────┐            ┌──────────────┐            ┌──────────────┐
           │ Document AI  │            │    Text      │            │   Vertex AI  │
           │              │            │  Chunking    │            │  Embeddings  │
           │ • Parse PDF  │───────────►│              │───────────►│              │
           │ • Extract    │            │ • 512 tokens │            │ gecko@004    │
           │   tables     │            │ • 50 overlap │            │ 768 dims     │
           │ • OCR images │            │              │            │              │
           └──────────────┘            └──────────────┘            └──────────────┘
                                                                          │
                                                                          ▼
                                                                  ┌──────────────┐
                                                                  │  Cloud SQL   │
                                                                  │  pgvector    │
                                                                  │              │
                                                                  │ Store chunks │
                                                                  │ + embeddings │
                                                                  └──────────────┘
```

### RAG Query Flow

```python
# Pseudocode for RAG query
async def rag_query(project_id: str, query: str, user_id: str):
    # 1. Generate query embedding
    query_embedding = await vertex_ai.embed(query)

    # 2. Vector similarity search
    chunks = await db.execute("""
        SELECT
            dc.content,
            dc.metadata,
            d.name as document_name,
            1 - (dc.embedding <=> $1) as similarity
        FROM document_chunks dc
        JOIN documents d ON d.id = dc.document_id
        WHERE d.project_id = $2
        ORDER BY dc.embedding <=> $1
        LIMIT 5
    """, [query_embedding, project_id])

    # 3. Build augmented prompt
    context = "\n\n".join([
        f"[From: {c.document_name}]\n{c.content}"
        for c in chunks
    ])

    prompt = f"""You are a project assistant with access to project documentation.

Context from project documents:
{context}

User question: {query}

Provide a helpful answer based on the context. Cite specific documents when referencing information."""

    # 4. Generate response
    response = await vertex_ai.generate(
        model="gemini-1.5-pro",
        prompt=prompt
    )

    # 5. Store in chat history
    await save_chat_message(project_id, user_id, query, response, chunks)

    return response
```

---

## AI Copilot Features

### Feature Set

| Feature | Description | Implementation |
|---------|-------------|----------------|
| **Risk Detection** | Identify tasks at risk of delay | Analyze dependencies + historical data |
| **Resource Optimization** | Suggest task redistribution | Load balancing algorithm + LLM suggestions |
| **Timeline Prediction** | Estimate project completion | ML model trained on historical projects |
| **Smart Scheduling** | Auto-suggest task dates | Dependency analysis + resource availability |
| **Executive Summaries** | Generate status reports | LLM summarization of project state |
| **Anomaly Detection** | Flag unusual patterns | Statistical analysis of task metrics |

### Copilot Prompt Template

```
You are an AI project management copilot for ProjectForge.

Current Project State:
- Project: {project_name}
- Client: {client_name}
- Timeline: {start_date} to {end_date}
- Progress: {completion_percentage}%
- At-risk tasks: {at_risk_count}

Recent Activity:
{recent_activity_summary}

Task Dependencies Graph:
{dependency_summary}

Resource Allocation:
{resource_summary}

Based on this information, provide:
1. Top 3 risks to project timeline
2. Recommended actions for this week
3. Resource reallocation suggestions if any bottlenecks exist

Be specific and actionable. Reference specific tasks and team members.
```

---

## Notification System

### Email Templates (React Email)

```tsx
// templates/task-assigned.tsx
import { Html, Head, Body, Container, Text, Button } from '@react-email/components';

interface TaskAssignedProps {
  recipientName: string;
  taskTitle: string;
  projectName: string;
  dueDate: string;
  assignedBy: string;
  taskUrl: string;
}

export default function TaskAssigned(props: TaskAssignedProps) {
  return (
    <Html>
      <Head />
      <Body style={styles.body}>
        <Container style={styles.container}>
          <Text style={styles.heading}>
            New Task Assigned
          </Text>
          <Text>
            Hi {props.recipientName},
          </Text>
          <Text>
            {props.assignedBy} has assigned you a new task in {props.projectName}:
          </Text>
          <Text style={styles.taskTitle}>
            {props.taskTitle}
          </Text>
          <Text>
            Due: {props.dueDate}
          </Text>
          <Button href={props.taskUrl} style={styles.button}>
            View Task
          </Button>
        </Container>
      </Body>
    </Html>
  );
}
```

### Notification Triggers

| Trigger | Condition | Recipients | Channels |
|---------|-----------|------------|----------|
| Task Assigned | On assignment creation | Assignee | Email, Slack, Teams |
| Due Date Near | 24h/48h/1w before due | Assignees | Email, Slack |
| Task Completed | Status → done | Project PM, dependents | Email, Slack |
| Task Overdue | Due date passed + not done | Assignee, PM | Email, Slack |
| Milestone Reached | All tasks in milestone done | All project members | Email |
| Document Uploaded | New document processed | Project members | Slack, Teams |

---

## API Design

### REST Endpoints

```yaml
# Organizations
GET    /api/v1/organizations
POST   /api/v1/organizations
GET    /api/v1/organizations/:id
PATCH  /api/v1/organizations/:id
DELETE /api/v1/organizations/:id

# Clients
GET    /api/v1/clients
POST   /api/v1/clients
GET    /api/v1/clients/:id
PATCH  /api/v1/clients/:id
DELETE /api/v1/clients/:id

# Projects
GET    /api/v1/projects
POST   /api/v1/projects
GET    /api/v1/projects/:id
PATCH  /api/v1/projects/:id
DELETE /api/v1/projects/:id
GET    /api/v1/projects/:id/gantt
GET    /api/v1/projects/:id/kanban

# Tasks
GET    /api/v1/projects/:projectId/tasks
POST   /api/v1/projects/:projectId/tasks
GET    /api/v1/tasks/:id
PATCH  /api/v1/tasks/:id
DELETE /api/v1/tasks/:id
POST   /api/v1/tasks/:id/dependencies
DELETE /api/v1/tasks/:id/dependencies/:depId
POST   /api/v1/tasks/:id/assignments
DELETE /api/v1/tasks/:id/assignments/:userId

# Milestones
GET    /api/v1/projects/:projectId/milestones
POST   /api/v1/projects/:projectId/milestones
PATCH  /api/v1/milestones/:id
DELETE /api/v1/milestones/:id

# Documents & RAG
GET    /api/v1/projects/:projectId/documents
POST   /api/v1/projects/:projectId/documents/upload
DELETE /api/v1/documents/:id
POST   /api/v1/projects/:projectId/chat
GET    /api/v1/projects/:projectId/chat/history

# AI Copilot
POST   /api/v1/projects/:projectId/copilot/analyze
POST   /api/v1/projects/:projectId/copilot/suggest
GET    /api/v1/projects/:projectId/copilot/risks

# Notifications
GET    /api/v1/notifications
PATCH  /api/v1/notifications/:id/read
GET    /api/v1/notification-preferences
PATCH  /api/v1/notification-preferences
```

### WebSocket Events

```typescript
// Firestore real-time events (via Firebase SDK)
interface TaskPositionUpdate {
  type: 'TASK_POSITION_UPDATE';
  taskId: string;
  position: number;
  status: TaskStatus;
  updatedBy: string;
  timestamp: number;
}

interface GanttStateUpdate {
  type: 'GANTT_STATE_UPDATE';
  projectId: string;
  viewMode: 'day' | 'week' | 'month';
  scrollPosition: number;
}
```

---

## Security Considerations

### Data Protection

| Layer | Protection |
|-------|------------|
| Transport | TLS 1.3 everywhere |
| Storage | Cloud SQL encryption at rest |
| Documents | Cloud Storage encryption + signed URLs |
| Secrets | Secret Manager with IAM |
| PII | Field-level encryption for sensitive data |

### Access Control

```
Organization Admin:
  - Full CRUD on organization settings
  - Manage members and roles
  - Access all clients and projects
  - View audit logs

Project Manager:
  - Full CRUD on assigned projects
  - Manage project members
  - Create/edit tasks and milestones
  - Access AI features

Collaborator:
  - View assigned projects
  - Update assigned tasks
  - Upload documents
  - Use RAG chat

Client (Read-only):
  - View assigned projects (filtered view)
  - View milestones and progress
  - Download shared documents
  - No task editing
```

---

## Deployment Strategy

### Environments

| Environment | Purpose | GCP Project |
|-------------|---------|-------------|
| Development | Local + feature testing | projectforge-dev |
| Staging | Integration testing | projectforge-staging |
| Production | Live users | projectforge-prod |

### CI/CD Pipeline

```yaml
# Cloud Build trigger on main branch
steps:
  # 1. Test
  - name: 'gcr.io/cloud-builders/npm'
    args: ['run', 'test']

  # 2. Build containers
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/api-gateway', './apps/api-gateway']

  # 3. Push to Artifact Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/api-gateway']

  # 4. Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    args:
      - 'run'
      - 'deploy'
      - 'api-gateway'
      - '--image=gcr.io/$PROJECT_ID/api-gateway'
      - '--region=us-central1'
      - '--platform=managed'
```

---

## Development Roadmap

### Phase 1: Foundation (Weeks 1-3)
- [ ] Monorepo setup with Turborepo
- [ ] GCP project configuration
- [ ] Terraform modules for core infrastructure
- [ ] Cloud SQL with schema and RLS
- [ ] Firebase Auth integration
- [ ] API Gateway scaffolding
- [ ] React app with auth flow

### Phase 2: Core Features (Weeks 4-7)
- [ ] Organizations, Clients, Projects CRUD
- [ ] Tasks with dependencies
- [ ] Gantt chart visualization
- [ ] Kanban board with drag-drop
- [ ] Firestore real-time sync
- [ ] User assignments and roles

### Phase 3: Notifications (Weeks 8-9)
- [ ] Resend integration
- [ ] React Email templates
- [ ] Cloud Tasks for scheduling
- [ ] Notification preferences
- [ ] Audit logging

### Phase 4: AI & RAG (Weeks 10-12)
- [ ] Document upload to Cloud Storage
- [ ] Document AI processing
- [ ] Vertex AI embeddings
- [ ] pgvector storage
- [ ] RAG chat interface
- [ ] AI Copilot features

### Phase 5: Integrations (Weeks 13-14)
- [ ] Slack bot (MCP)
- [ ] Teams integration
- [ ] Webhook system
- [ ] Client Portal view

### Phase 6: Polish (Weeks 15-16)
- [ ] Performance optimization
- [ ] Mobile responsiveness
- [ ] White-label branding
- [ ] Documentation
- [ ] Load testing

---

## Cost Estimation (Monthly)

| Service | Estimated Cost | Notes |
|---------|----------------|-------|
| Cloud Run | $50-150 | 4 services, auto-scaling |
| Cloud SQL | $50-100 | db-f1-micro to db-g1-small |
| Cloud Storage | $10-30 | Documents, backups |
| Firestore | $10-25 | Real-time sync only |
| Vertex AI | $50-200 | Embeddings + Gemini |
| Document AI | $10-50 | Pay per page |
| Cloud Tasks/Pub/Sub | $5-15 | Event processing |
| Resend | $20-50 | Email volume |
| **Total** | **$205-620** | Scales with usage |

---

## Appendix

### Useful Commands

```bash
# Local development
turbo dev

# Run specific service
turbo dev --filter=api-gateway

# Deploy to staging
terraform -chdir=infrastructure/terraform/environments/staging apply

# Run migrations
npm run db:migrate

# Generate types from schema
npm run db:generate

# Run all tests
turbo test

# Build all services
turbo build
```

### Reference Links

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [Firebase Auth](https://firebase.google.com/docs/auth)
- [pgvector](https://github.com/pgvector/pgvector)
- [Resend](https://resend.com/docs)
- [React Email](https://react.email)
- [shadcn/ui](https://ui.shadcn.com)

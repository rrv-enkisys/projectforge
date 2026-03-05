# ProjectForge - Estado Actual

**Fecha:** 2026-03-02
**Commit:** `877b76e` — fix(ai-service): add missing document extraction dependencies
**Branch:** `main`
**Commits últimos 30 días:** 72

---

## Resumen Ejecutivo

ProjectForge está en un estado de **desarrollo avanzado y funcional**. Los 4 servicios backend (API Gateway Go, Core Service Python, AI Service Python, Notification Service Go) tienen imágenes Docker buildeadas y publicadas en Artifact Registry, con el pipeline de CI/CD (GitHub Actions + WIF) completamente operativo. El frontend React compila sin errores TypeScript, con 13 páginas y 8 módulos de features implementados incluyendo Kanban DnD, Gantt Chart, Chat AI con streaming, RAG de documentos y Copilot de proyectos. La infraestructura dev de GCP fue desplegada vía Terraform, aunque la sesión gcloud local está caducada y no se puede verificar el estado live de Cloud Run en este momento. Los bloqueantes principales son: migraciones de base de datos pendientes de aplicar en Cloud SQL, DNS sin configurar, y Firebase con credenciales placeholder.

---

## Servicios Backend

| Servicio | Puerto | Imagen Docker | Endpoints | Tests |
|----------|--------|---------------|-----------|-------|
| API Gateway | 8080 | `api-gateway:latest` (52MB) | `/health` + proxy routes | proxy, auth, cors, metrics, ratelimit, tenant |
| Core Service | 8081 | `core-service:latest` (1.29GB) | 48+ endpoints REST | integration (projects, tasks, relations) + unit |
| AI Service | 8082 | `ai-service:latest` (1.37GB) | 19+ endpoints AI | unit (analyzer, chunker) + integration |
| Notification Service | 8083 | `notification-service:latest` (30MB) | notifications + webhooks | email, inapp, webhook |

> **Nota:** Servicios no corriendo localmente. Estado live en Cloud Run no verificable — sesión `gcloud` caducada (`reauth related error`). Ejecutar `gcloud auth login` para restaurar acceso.

### Core Service — Routers disponibles

| Router | Endpoints |
|--------|-----------|
| `/api/v1/clients` | 5 |
| `/api/v1/projects` | 6 |
| `/api/v1/tasks` | 10 (incluyendo bulk, search, status) |
| `/api/v1/tasks/{id}/dependencies` | completo (CRUD + cycle detection) |
| `/api/v1/tasks/{id}/assignments` | completo |
| `/api/v1/tasks/{id}/comments` | completo |
| `/api/v1/milestones` | 6 |
| `/api/v1/users` | 10 |
| `/api/v1/organizations` | completo |
| `/api/v1/dashboard` | 1 |

### AI Service — Routers disponibles

| Módulo | Endpoints |
|--------|-----------|
| `/api/v1/rag` | `POST /query`, `POST /query/stream` |
| `/api/v1/chat` | sesiones CRUD + mensajes + streaming (8 endpoints) |
| `/api/v1/copilot` | `/analyze`, `/risks`, `/suggestions`, `/timeline` (4 endpoints) |
| `/api/v1/documents` | upload, list, get, delete, process (5 endpoints) |

---

## Infraestructura GCP

| Recurso | Estado | Detalles |
|---------|--------|----------|
| GCP Auth local | ❌ Caducada | `reauth related error` — ejecutar `gcloud auth login` |
| Terraform state | ❌ Inaccesible | Auth caducada para GCS backend |
| Cloud Run (dev) | ⚠️ Último conocido ✅ | 4 servicios desplegados (`*-dev-memn77o6ia-uc.a.run.app`) |
| Artifact Registry | ✅ | 4 imágenes publicadas con tag `latest` |
| Cloud SQL | ⚠️ Desplegado | IP privada `10.221.0.3` — migraciones pendientes |
| Load Balancer | ✅ | IP `35.244.226.31` |
| DNS `dev.projectforge.app` | ❌ Pendiente | No apunta a LB IP `35.244.226.31` |
| Terraform staging/prod | ❌ No desplegado | Solo `dev` aplicado |
| Firebase credentials | ⚠️ Placeholder | Usa `{}` → ADC fallback en Cloud Run |

### Imágenes en Artifact Registry (`us-central1-docker.pkg.dev/projectforge-4314f/projectforge/`)

| Imagen | Tag | Tamaño comprimido |
|--------|-----|-------------------|
| `api-gateway` | `latest` | 16.7MB |
| `notification-service` | `latest` | 9.65MB |
| `core-service` | `latest` | 354MB |
| `ai-service` | `latest` | 397MB |

---

## Frontend (React)

| Métrica | Estado |
|---------|--------|
| Build TypeScript | ✅ 0 errores TS |
| Páginas implementadas | 13 |
| Feature modules | 8 |
| Dockerfile | ✅ existe |

### Páginas (`apps/web/src/pages/`)

`ChatPage`, `ClientsPage`, `DashboardPage`, `DocumentsPage`, `HomePage`, `LoginPage`, `MilestonesPage`, `NotFoundPage`, `ProjectDetailPage`, `ProjectsPage`, `SettingsPage`, `SignupPage`, `TasksPage`

### Feature Modules (`apps/web/src/features/`)

| Módulo | Componentes destacados |
|--------|----------------------|
| `ai` | `ChatPanel`, `CopilotPanel`, `DocumentQAPanel` |
| `tasks` | `KanbanBoard`, `KanbanCard`, `KanbanColumn`, `TaskFormDialog`, `TaskForm` |
| `projects` | `GanttChart`, `GanttWrapper`, `ProjectCard`, `ProjectForm`, `ProjectFormDialog` |
| `milestones` | `MilestoneForm`, `MilestoneFormDialog` |
| `documents` | (page-level) |
| `dashboard` | (widgets) |
| `notifications` | `NotificationBell` |
| `clients` | (CRUD) |

### Dependencias clave

| Paquete | Versión |
|---------|---------|
| `@dnd-kit/core` | ^6.3.1 |
| `@dnd-kit/sortable` | ^10.0.0 |
| `frappe-gantt` | ^1.2.1 |
| `@tanstack/react-query` | ^5.17.0 |
| `zustand` | ^4.5.0 |
| `firebase` | ^10.7.2 |

---

## Módulos de AI

| Módulo | Backend (AI Service) | Gateway (proxy) | Frontend |
|--------|---------------------|-----------------|----------|
| Chat | ✅ `chat/router.py` (streaming) | ✅ `/api/v1/chat/*` | ✅ `ChatPanel.tsx` + `ChatPage.tsx` |
| RAG (Doc Q&A) | ✅ `rag/router.py` (query + stream) | ✅ `/api/v1/rag/*` | ✅ `DocumentQAPanel.tsx` |
| Copilot | ✅ `copilot/router.py` (4 análisis) | ✅ `/api/v1/copilot/*` | ✅ `CopilotPanel.tsx` |
| Documents | ✅ `documents/router.py` (5 ops) | ✅ `/api/v1/documents/*` | ✅ `DocumentsPage.tsx` |
| Embeddings | ✅ `embeddings/` (chunker + vertex_client) | N/A | N/A |
| Extractor | ✅ `documents/extractor.py` | N/A | N/A |

### Componentes del pipeline RAG

- `embeddings/chunker.py` — tokenización (512 tokens, 50 overlap)
- `embeddings/vertex_client.py` — Vertex AI `text-embedding-004` (gecko) para embeddings, `gemini-2.0-flash` para generación
- `embeddings/service.py` — orquestación
- `documents/processor.py` — Document AI integration
- `documents/storage.py` — Cloud Storage
- `rag/prompts.py` — prompt templates
- `copilot/project_data.py` — `ProjectDataRepository` con queries SQL enriquecidas (client + assignees)

---

## Features Críticos

| Feature | Estado | Notas |
|---------|--------|-------|
| Kanban DnD | ✅ Implementado | `KanbanBoard.tsx` con `DndContext` + `@dnd-kit/core` |
| Gantt Chart | ✅ Implementado | `GanttChart.tsx` + `GanttWrapper.tsx` con `frappe-gantt` |
| Task Dependencies | ✅ Implementado | `dependencies_router.py` con detección de ciclos (DFS) |
| Task Bulk Operations | ✅ Implementado | `POST/PATCH/DELETE /tasks/bulk` |
| Task Search | ✅ Implementado | `POST /tasks/search` |
| Chat AI Streaming | ✅ Implementado | `POST /chat/messages/stream` |
| RAG Doc Q&A | ✅ Implementado | `POST /rag/query/stream` |
| Copilot Project Analysis | ✅ Implementado | risks, suggestions, timeline |
| Multi-tenancy RLS | ✅ Implementado | Migration 000003 + `organization_id` en todas las tablas |
| Document Processing | ✅ Código listo | Depende de Cloud SQL con pgvector y migraciones aplicadas |
| Notification Email | ✅ Implementado | Resend API |
| Notification Slack | ✅ Implementado | Slack Bot |
| Notification Webhooks | ✅ Implementado | configurable |
| Dashboard Stats | ⚠️ Parcial | `documents=0` hardcodeado (TODO pendiente) |
| Firebase Auth | ⚠️ Placeholder | ADC fallback en Cloud Run — funcional pero sin credenciales reales |

---

## CI/CD

| Workflow | Trigger | Estado |
|----------|---------|--------|
| `ci.yml` | PR → main | ✅ lint + tests + docker build check |
| `deploy-dev.yml` | push → main | ✅ build + push Artifact Registry + deploy Cloud Run |
| `deploy-prod.yml` | release published | ✅ staging → smoke tests → manual approval → blue-green prod |

- **Auth GCP:** Workload Identity Federation (sin SA keys — org policy `iam.disableServiceAccountKeyCreation`)
- **pnpm version:** `9.0.0` (alineado en proyecto y CI)
- **Environments:** `dev` (auto), `staging` (auto), `production` (required reviewer: rrv-enkisys)

---

## Migraciones de Base de Datos

| Migración | Descripción | Estado en Cloud SQL |
|-----------|-------------|---------------------|
| 000001 | Initial schema (orgs, users) | ⚠️ Desconocido |
| 000002 | Projects + Tasks | ⚠️ Desconocido |
| 000003 | Enable RLS policies | ⚠️ Desconocido |
| 000004 | Documents + RAG (pgvector) | ⚠️ Desconocido |
| 000005 | Notifications | ⚠️ Desconocido |
| 000006 | Audit Log | ⚠️ Desconocido |
| 000007 | Budget en projects | ⚠️ Desconocido |
| 000008 | Align AI service models (crítica) | ⚠️ Desconocido |

> Las migraciones no se aplican automáticamente. Requieren `gcloud sql connect` + `migrate` CLI o script manual.

---

## Bugs Conocidos

| # | Bug | Severidad | Ubicación |
|---|-----|-----------|-----------|
| 1 | `documents=0` hardcodeado en dashboard — no llama al AI service | Baja | `core-service/src/dashboard/service.py:113` |
| 2 | Tests de integración AI service omitidos en CI (requieren DB) | Baja | `ci.yml` — solo corre `tests/unit/` |
| 3 | GCP auth local caducada — imposible verificar estado Cloud Run | Media (operativa) | VM local |
| 4 | DNS `dev.projectforge.app` no apunta al LB IP `35.244.226.31` | Media | DNS externo |
| 5 | Migraciones BD pendientes — servicios fallarán en primera query si no aplicadas | Alta | Cloud SQL |
| 6 | Firebase placeholder `{}` — en local no autentica usuarios reales | Media | `api-gateway/firebase/client.go` |
| 7 | Staging/prod Terraform no desplegado — deploy-prod.yml fallará | Alta | `infrastructure/terraform/environments/` |

---

## Commits Recientes (últimos 20)

```
877b76e fix(ai-service): add missing document extraction dependencies
dd3a594 fix(documents): fix multipart upload 502 by removing explicit Content-Type
338df9d fix(chat): replace nested button with div role=button in session list
bb25c69 feat(frontend): add Document Q&A panel with RAG integration
01658fa feat(copilot): enrich project data with client name and task assignees
e73b203 fix(chat): improve fallback message to distinguish rate limit vs credentials
486ade7 feat(ai): add live project context to Chat AI responses
dd73c06 fix(ai): fix timezone comparison and missing schema fields in copilot
292c5ad fix(ci): remove redundant health check
f75e200 fix(ci): replace curl health check with gcloud Ready status check
dd9b5e0 fix(ci): switch to Workload Identity Federation (no SA key JSON)
370b06d feat(ci): add GitHub Actions workflows for CI/CD pipeline
2e20f46 fix(ai): correct 3 critical bugs in copilot/RAG pipeline
8902b5c fix(gateway): use credentials JSON instead of file path for Firebase
ebed8de fix(docker): update Go version and fix ai-service entrypoint
df7afa8 fix(infra): remove reserved PORT env var and fix uniform bucket access
4b660bf fix(infra): expand replication.auto{} blocks in secret-manager module
49d789f feat(infra): complete Terraform GCP infrastructure for ProjectForge
118faec feat: implement Kanban DnD, Gantt chart, task relations API, and fix TS errors
202a4b3 fix: resolve full-system test issues - chat, copilot, kanban, documents
```

---

## Agents Configurados (`.claude/agents/`)

| Agent | Propósito |
|-------|-----------|
| `architect` | Decisiones de arquitectura del sistema |
| `database` | Schema, migraciones, pgvector |
| `frontend` | React/TypeScript/shadcn UI |
| `backend-python` | FastAPI/SQLAlchemy/AI service |
| `backend-go` | Gateway/Chi router/middleware |
| `gcp-infra` | Cloud Run/Cloud SQL/Secret Manager |
| `cicd-github` | GitHub Actions workflows |
| `gantt-chart` | frappe-gantt implementation |
| `kanban-dnd` | @dnd-kit DnD Kanban |
| `task-relations` | Task dependencies y relaciones |
| `terraform-gcp` | Terraform IaC GCP |

---

## Próximos Pasos Recomendados

| # | Paso | Prioridad | Notas |
|---|------|-----------|-------|
| 1 | **Renovar auth GCP** (`gcloud auth login`) | CRÍTICA | Desbloquea todas las operaciones cloud |
| 2 | **Aplicar migraciones 001–008 en Cloud SQL** | CRÍTICA | Sin esto los servicios fallan en runtime |
| 3 | **Configurar DNS** `dev.projectforge.app → 35.244.226.31` | Alta | Necesario para testing end-to-end |
| 4 | **Desplegar Terraform staging** (`terraform apply` en `/environments/staging`) | Alta | Prerequisito para pipeline de producción |
| 5 | **Firebase credentials reales** (reemplazar placeholder `{}`) | Alta | Necesario para autenticación de usuarios reales |
| 6 | **Verificar health de Cloud Run** (`gcloud run services list`) | Media | Confirmar que los 4 servicios siguen `Ready` |
| 7 | **Corregir dashboard document count** — llamar al AI service en lugar de hardcodear 0 | Baja | `dashboard/service.py:113` |
| 8 | **Tests de integración AI service en CI** — agregar servicio postgres al job `test-ai-service` | Baja | Mayor cobertura en CI |
| 9 | **Desplegar Terraform prod** | Baja | Solo cuando staging esté estable |
| 10 | **Implementar frontend para Task Dependencies** — el backend existe pero falta UI | Media | `dependencies_router.py` completo, falta UI en `TasksPage` |

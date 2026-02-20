# Task Relations Agent

You are a focused Python backend specialist for ProjectForge. Your sole responsibility is to implement the three sub-resource APIs for tasks: dependencies, assignments, and comments — inside the existing `core-service`.

## Objective

Create three new routers within `apps/core-service/src/tasks/` following the exact patterns of the existing codebase:
- `dependencies_router.py` — manage finish-to-start and other dependency types between tasks
- `assignments_router.py` — manage user assignments with roles per task
- `comments_router.py` — manage text comments on tasks

Each router must be registered in `main.py` as a top-level router.

## Schema Real en la Base de Datos (migración 000002_projects_tasks.up.sql)

> **IMPORTANTE**: El schema real difiere del briefing inicial. Usa estos datos de la migración:

```sql
-- task_dependencies (NO tiene lag_days — el briefing es incorrecto en ese punto)
CREATE TABLE task_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    depends_on_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    dependency_type dependency_type NOT NULL DEFAULT 'finish_to_start',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(task_id, depends_on_id),
    CHECK (task_id != depends_on_id)
);

-- task_assignments (NO tiene assigned_at — tiene created_at/updated_at)
CREATE TABLE task_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role assignment_role NOT NULL DEFAULT 'responsible',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(task_id, user_id, role)
);

-- task_comments
CREATE TABLE task_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

ENUMs ya existentes en la DB:
- `dependency_type`: `'finish_to_start'`, `'start_to_start'`, `'finish_to_finish'`, `'start_to_finish'`
- `assignment_role`: `'responsible'`, `'participant'`, `'reviewer'`

RLS ya habilitado en las 3 tablas con policy `organization_id = current_setting('app.current_organization_id')::uuid`.

## Estructura del Core Service Existente

```
apps/core-service/src/
├── main.py                   ← Registrar los 3 nuevos routers aquí
├── database.py               ← set_organization_context(), get_db(), Base
├── common/
│   ├── dependencies.py       ← DatabaseSession, OrganizationId, AuthenticatedUser, CurrentUser
│   └── exceptions.py         ← NotFoundError, BusinessRuleError, ConflictError, ValidationError
└── tasks/
    ├── models.py             ← Task, TaskStatus, TaskPriority
    ├── repository.py         ← TaskRepository (tiene get_ancestors() para cycle detection)
    ├── service.py            ← TaskService
    ├── schemas.py            ← TaskResponse, TaskCreate, etc.
    ├── router.py             ← router = APIRouter(prefix="/tasks")
    ├── dependencies_router.py  ← CREAR
    ├── assignments_router.py   ← CREAR
    └── comments_router.py      ← CREAR
```

## Patrón de Implementación Obligatorio

Cada nueva entidad sigue este patrón (sin Service layer separado para mantener simplicidad — la lógica de negocio va directamente en el Repository):

### 1. Models (añadir a tasks/models.py)

Los tres modelos SQLAlchemy deben añadirse al archivo `tasks/models.py` existente, NO crear archivos separados de models:

```python
from sqlalchemy import Enum as SAEnum

class DependencyType(str, PyEnum):
    FINISH_TO_START = "finish_to_start"
    START_TO_START = "start_to_start"
    FINISH_TO_FINISH = "finish_to_finish"
    START_TO_FINISH = "start_to_finish"

class AssignmentRole(str, PyEnum):
    RESPONSIBLE = "responsible"
    PARTICIPANT = "participant"
    REVIEWER = "reviewer"

class TaskDependency(Base):
    __tablename__ = "task_dependencies"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id: Mapped[UUID] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    depends_on_id: Mapped[UUID] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    dependency_type: Mapped[str] = mapped_column(
        SAEnum(DependencyType, name="dependency_type", create_type=False, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False, default="finish_to_start",
    )
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now(), onupdate=func.now())

class TaskAssignment(Base):
    __tablename__ = "task_assignments"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id: Mapped[UUID] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(
        SAEnum(AssignmentRole, name="assignment_role", create_type=False, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False, default="responsible",
    )
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now(), onupdate=func.now())

class TaskComment(Base):
    __tablename__ = "task_comments"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id: Mapped[UUID] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now(), onupdate=func.now())
```

**Usar `create_type=False`** en los Enum de SQLAlchemy — los tipos ya existen en la DB, no recrearlos.

### 2. Dependency de CurrentUser → User UUID

`CurrentUser.uid` es un Firebase UID (`str`), pero `task_assignments.user_id` y `task_comments.user_id` referencian `users.id` (UUID). Se necesita hacer un lookup en la tabla `users`:

```python
# En cada repository que necesite user_id:
async def _get_user_uuid_by_firebase_uid(self, firebase_uid: str) -> UUID:
    from ..users.models import User  # evitar import circular
    result = await self.db.execute(
        select(User.id).where(User.firebase_uid == firebase_uid)
    )
    user_id = result.scalar_one_or_none()
    if not user_id:
        raise NotFoundError("User", firebase_uid)
    return user_id
```

### 3. Patrón del Router

Cada router usa el mismo patrón de dependency injection:

```python
from fastapi import APIRouter, Depends, status
from ..common.dependencies import DatabaseSession, OrganizationId, AuthenticatedUser

router = APIRouter(prefix="/tasks/{task_id}/dependencies", tags=["task-dependencies"])

def get_repo(db: DatabaseSession, org_id: OrganizationId) -> TaskDependencyRepository:
    return TaskDependencyRepository(db, org_id)
```

### 4. Registro en main.py

Añadir en `main.py` junto a los otros routers existentes:

```python
from .tasks.dependencies_router import router as task_dependencies_router
from .tasks.assignments_router import router as task_assignments_router
from .tasks.comments_router import router as task_comments_router

# En la sección de include_router:
app.include_router(task_dependencies_router, prefix=settings.api_prefix)
app.include_router(task_assignments_router, prefix=settings.api_prefix)
app.include_router(task_comments_router, prefix=settings.api_prefix)
```

## Especificación Completa por Recurso

---

### A. Task Dependencies (`dependencies_router.py`)

**Repository: `TaskDependencyRepository`**

```python
class TaskDependencyRepository:
    def __init__(self, db: AsyncSession, organization_id: UUID): ...
    async def _set_context(self): ...

    async def list(self, task_id: UUID) -> list[TaskDependency]: ...
    async def get(self, task_id: UUID, dep_id: UUID) -> TaskDependency: ...
    async def create(self, task_id: UUID, depends_on_id: UUID, dependency_type: DependencyType) -> TaskDependency: ...
    async def delete(self, task_id: UUID, dep_id: UUID) -> None: ...
```

**Schemas:**
```python
class TaskDependencyCreate(BaseModel):
    depends_on_id: UUID
    dependency_type: DependencyType = DependencyType.FINISH_TO_START

class TaskDependencyResponse(BaseModel):
    id: UUID
    task_id: UUID
    depends_on_id: UUID
    dependency_type: DependencyType
    organization_id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
```

**Endpoints:**
```
GET    /api/v1/tasks/{task_id}/dependencies           → list[TaskDependencyResponse]
POST   /api/v1/tasks/{task_id}/dependencies           → TaskDependencyResponse (201)
DELETE /api/v1/tasks/{task_id}/dependencies/{dep_id}  → 204
```

**Validaciones de negocio obligatorias:**
1. La `task_id` debe existir y pertenecer a la organización (usar `TaskRepository.get_by_id`)
2. La `depends_on_id` debe existir y pertenecer a la misma organización
3. Ambas tasks deben pertenecer al mismo proyecto (`task.project_id == depends_on.project_id`)
4. **Detección de ciclo**: Antes de crear, verificar que `depends_on_id` no dependa (directa o transitivamente) de `task_id`. Usar el método `get_ancestors()` existente en `TaskRepository` como referencia para implementar un traversal similar en `TaskDependencyRepository`. Lanzar `BusinessRuleError("Circular dependency detected", rule="circular_dependency")` si se detecta.
5. La constraint `CHECK (task_id != depends_on_id)` ya está en DB — capturar `IntegrityError` si ocurre y lanzar `BusinessRuleError`
6. La constraint `UNIQUE(task_id, depends_on_id)` ya está en DB — capturar `IntegrityError` y lanzar `ConflictError("Dependency already exists")`

---

### B. Task Assignments (`assignments_router.py`)

**Repository: `TaskAssignmentRepository`**

```python
class TaskAssignmentRepository:
    def __init__(self, db: AsyncSession, organization_id: UUID): ...
    async def _set_context(self): ...
    async def _get_user_uuid_by_firebase_uid(self, firebase_uid: str) -> UUID: ...

    async def list(self, task_id: UUID) -> list[TaskAssignment]: ...
    async def get(self, task_id: UUID, user_id: UUID, role: AssignmentRole) -> TaskAssignment: ...
    async def create(self, task_id: UUID, user_id: UUID, role: AssignmentRole) -> TaskAssignment: ...
    async def delete(self, task_id: UUID, assignment_id: UUID) -> None: ...
```

**Schemas:**
```python
class TaskAssignmentCreate(BaseModel):
    user_id: UUID                      # UUID del usuario en la tabla users (no Firebase UID)
    role: AssignmentRole = AssignmentRole.RESPONSIBLE

class TaskAssignmentResponse(BaseModel):
    id: UUID
    task_id: UUID
    user_id: UUID
    role: AssignmentRole
    organization_id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
```

**Endpoints:**
```
GET    /api/v1/tasks/{task_id}/assignments              → list[TaskAssignmentResponse]
POST   /api/v1/tasks/{task_id}/assignments              → TaskAssignmentResponse (201)
DELETE /api/v1/tasks/{task_id}/assignments/{assignment_id}  → 204
```

**Validaciones de negocio:**
1. `task_id` debe existir y pertenecer a la organización
2. `user_id` en el body es el UUID interno del usuario (no Firebase UID) — verificar que existe en `users` table
3. El usuario asignado debe ser miembro de la organización (verificar en `organization_members`)
4. La constraint `UNIQUE(task_id, user_id, role)` está en DB — capturar `IntegrityError` y lanzar `ConflictError("User already assigned with this role")`
5. El DELETE usa `assignment_id` (UUID del registro en `task_assignments`), no `user_id`

---

### C. Task Comments (`comments_router.py`)

**Repository: `TaskCommentRepository`**

```python
class TaskCommentRepository:
    def __init__(self, db: AsyncSession, organization_id: UUID): ...
    async def _set_context(self): ...
    async def _get_user_uuid_by_firebase_uid(self, firebase_uid: str) -> UUID: ...

    async def list(self, task_id: UUID) -> list[TaskComment]: ...
    async def get(self, task_id: UUID, comment_id: UUID) -> TaskComment: ...
    async def create(self, task_id: UUID, user_id: UUID, content: str) -> TaskComment: ...
    async def update(self, task_id: UUID, comment_id: UUID, content: str, author_user_id: UUID) -> TaskComment: ...
    async def delete(self, task_id: UUID, comment_id: UUID, author_user_id: UUID) -> None: ...
```

**Schemas:**
```python
class TaskCommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)

class TaskCommentUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)

class TaskCommentResponse(BaseModel):
    id: UUID
    task_id: UUID
    user_id: UUID
    content: str
    organization_id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
```

**Endpoints:**
```
GET    /api/v1/tasks/{task_id}/comments                       → list[TaskCommentResponse]
POST   /api/v1/tasks/{task_id}/comments                       → TaskCommentResponse (201)
PATCH  /api/v1/tasks/{task_id}/comments/{comment_id}          → TaskCommentResponse
DELETE /api/v1/tasks/{task_id}/comments/{comment_id}          → 204
```

**Validaciones de negocio:**
1. `task_id` debe existir y pertenecer a la organización
2. `user_id` del comentario se obtiene via `_get_user_uuid_by_firebase_uid(current_user.uid)` — **no viene del body, viene del token**
3. **Autoría**: Solo el autor puede editar o borrar su propio comentario. Verificar `comment.user_id == current_user_uuid` antes de update/delete. Lanzar `PermissionDeniedError("Only the comment author can edit or delete this comment")` si no coincide.
4. GET no requiere autoría — cualquier miembro de la organización puede ver todos los comentarios
5. Ordenar por `created_at ASC` en el listado (conversación cronológica)

**Cómo obtener current_user en los routers de comments y assignments:**
```python
from ..common.dependencies import AuthenticatedUser

@router.post("", ...)
async def create_comment(
    task_id: UUID,
    data: TaskCommentCreate,
    current_user: AuthenticatedUser,    # ← obtiene CurrentUser con .uid (Firebase UID)
    repo: TaskCommentRepository = Depends(get_repo),
) -> TaskCommentResponse:
    user_uuid = await repo._get_user_uuid_by_firebase_uid(current_user.uid)
    ...
```

## Manejo de Errores

Usar las excepciones existentes del proyecto, NO lanzar HTTPException directamente:

```python
from ..common.exceptions import (
    NotFoundError,         # → 404
    BusinessRuleError,     # → 422 con rule
    ConflictError,         # → 409
    PermissionDeniedError, # → 403
)
```

Capturar `sqlalchemy.exc.IntegrityError` en los repositories para convertirlos en `ConflictError` o `BusinessRuleError` según el caso, dentro del bloque try/except con rollback:

```python
from sqlalchemy.exc import IntegrityError

try:
    self.db.add(record)
    await self.db.flush()
    await self.db.commit()
    await self.db.refresh(record)
    return record
except IntegrityError as e:
    await self.db.rollback()
    if "unique" in str(e.orig).lower():
        raise ConflictError("Dependency already exists")
    raise
except Exception:
    await self.db.rollback()
    raise
```

## Checklist de Entrega

- [ ] `DependencyType`, `AssignmentRole`, `TaskDependency`, `TaskAssignment`, `TaskComment` añadidos a `tasks/models.py`
- [ ] `dependencies_router.py` creado con GET, POST, DELETE endpoints
- [ ] `assignments_router.py` creado con GET, POST, DELETE endpoints
- [ ] `comments_router.py` creado con GET, POST, PATCH, DELETE endpoints
- [ ] Cada router tiene su Repository class en el mismo archivo (no Service layer separado)
- [ ] Validación de ciclo en dependencies implementada
- [ ] `user_id` en assignments/comments se resuelve desde Firebase UID via lookup a tabla `users`
- [ ] Autoría verificada en PATCH/DELETE de comments
- [ ] IntegrityError capturado y convertido a ConflictError en todos los repositories
- [ ] Los 3 routers registrados en `main.py`
- [ ] `mypy --strict` sin errores (usar `# type: ignore` solo donde sea inevitable)
- [ ] Sin migraciones nuevas necesarias (schema ya existe en DB)

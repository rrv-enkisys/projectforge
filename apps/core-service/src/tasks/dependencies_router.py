"""Router, repository, and schemas for task dependencies."""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.dependencies import DatabaseSession, OrganizationId
from ..common.exceptions import BusinessRuleError, ConflictError, NotFoundError
from ..database import set_organization_context
from .models import DependencyType, Task, TaskDependency

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------


class TaskDependencyRepository:
    def __init__(self, db: AsyncSession, organization_id: UUID) -> None:
        self.db = db
        self.organization_id = organization_id

    async def _set_context(self) -> None:
        await set_organization_context(self.db, self.organization_id)

    async def _get_task(self, task_id: UUID) -> Task:
        """Fetch a task, asserting org ownership."""
        await self._set_context()
        result = await self.db.execute(
            select(Task).where(
                Task.id == task_id,
                Task.organization_id == self.organization_id,
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            raise NotFoundError("Task", str(task_id))
        return task

    async def _would_create_cycle(self, task_id: UUID, depends_on_id: UUID) -> bool:
        """Return True if adding (task_id depends on depends_on_id) would create a cycle.

        Performs a BFS starting from depends_on_id, following outgoing dependency
        edges. If we reach task_id, a cycle would be formed.
        """
        await self._set_context()
        visited: set[UUID] = set()
        queue: list[UUID] = [depends_on_id]

        while queue:
            current = queue.pop(0)
            if current == task_id:
                return True
            if current in visited:
                continue
            visited.add(current)

            result = await self.db.execute(
                select(TaskDependency.depends_on_id).where(
                    TaskDependency.task_id == current,
                    TaskDependency.organization_id == self.organization_id,
                )
            )
            for dep_id in result.scalars().all():
                if dep_id not in visited:
                    queue.append(dep_id)

        return False

    async def list(self, task_id: UUID) -> list[TaskDependency]:
        await self._get_task(task_id)
        result = await self.db.execute(
            select(TaskDependency).where(
                TaskDependency.task_id == task_id,
                TaskDependency.organization_id == self.organization_id,
            )
        )
        return list(result.scalars().all())

    async def create(
        self, task_id: UUID, data: TaskDependencyCreate
    ) -> TaskDependency:
        task = await self._get_task(task_id)
        dep_task = await self._get_task(data.depends_on_id)

        if task.project_id != dep_task.project_id:
            raise BusinessRuleError(
                "Both tasks must belong to the same project",
                rule="same_project_required",
            )

        if await self._would_create_cycle(task_id, data.depends_on_id):
            raise BusinessRuleError(
                "Circular dependency detected",
                rule="circular_dependency",
            )

        try:
            record = TaskDependency(
                task_id=task_id,
                depends_on_id=data.depends_on_id,
                dependency_type=data.dependency_type.value,
                organization_id=self.organization_id,
            )
            self.db.add(record)
            await self.db.flush()
            await self.db.commit()
            await self.db.refresh(record)
            return record
        except IntegrityError as e:
            await self.db.rollback()
            err_str = str(e.orig).lower()
            if "unique" in err_str:
                raise ConflictError("Dependency already exists")
            if "check" in err_str:
                raise BusinessRuleError(
                    "A task cannot depend on itself",
                    rule="self_dependency",
                )
            raise
        except Exception:
            await self.db.rollback()
            raise

    async def delete(self, task_id: UUID, dep_id: UUID) -> None:
        await self._set_context()
        result = await self.db.execute(
            select(TaskDependency).where(
                TaskDependency.id == dep_id,
                TaskDependency.task_id == task_id,
                TaskDependency.organization_id == self.organization_id,
            )
        )
        record = result.scalar_one_or_none()
        if not record:
            raise NotFoundError("TaskDependency", str(dep_id))
        try:
            await self.db.delete(record)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/tasks/{task_id}/dependencies", tags=["task-dependencies"])


def get_repo(db: DatabaseSession, org_id: OrganizationId) -> TaskDependencyRepository:
    return TaskDependencyRepository(db, org_id)


@router.get("", response_model=list[TaskDependencyResponse])
async def list_dependencies(
    task_id: UUID,
    repo: TaskDependencyRepository = Depends(get_repo),
) -> list[TaskDependency]:
    return await repo.list(task_id)


@router.post(
    "",
    response_model=TaskDependencyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_dependency(
    task_id: UUID,
    data: TaskDependencyCreate,
    repo: TaskDependencyRepository = Depends(get_repo),
) -> TaskDependency:
    return await repo.create(task_id, data)


@router.delete("/{dep_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dependency(
    task_id: UUID,
    dep_id: UUID,
    repo: TaskDependencyRepository = Depends(get_repo),
) -> None:
    await repo.delete(task_id, dep_id)

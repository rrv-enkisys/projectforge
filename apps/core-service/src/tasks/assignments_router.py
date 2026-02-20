"""Router, repository, and schemas for task assignments."""
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
from .models import AssignmentRole, Task, TaskAssignment

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class TaskAssignmentCreate(BaseModel):
    user_id: UUID
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


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------


class TaskAssignmentRepository:
    def __init__(self, db: AsyncSession, organization_id: UUID) -> None:
        self.db = db
        self.organization_id = organization_id

    async def _set_context(self) -> None:
        await set_organization_context(self.db, self.organization_id)

    async def _get_task(self, task_id: UUID) -> Task:
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

    async def _verify_user_exists(self, user_id: UUID) -> None:
        """Verify the user exists in the users table."""
        from ..users.models import User  # avoid circular import

        result = await self.db.execute(select(User.id).where(User.id == user_id))
        if not result.scalar_one_or_none():
            raise NotFoundError("User", str(user_id))

    async def list(self, task_id: UUID) -> list[TaskAssignment]:
        await self._get_task(task_id)
        result = await self.db.execute(
            select(TaskAssignment).where(
                TaskAssignment.task_id == task_id,
                TaskAssignment.organization_id == self.organization_id,
            )
        )
        return list(result.scalars().all())

    async def create(self, task_id: UUID, data: TaskAssignmentCreate) -> TaskAssignment:
        await self._get_task(task_id)
        await self._verify_user_exists(data.user_id)

        try:
            record = TaskAssignment(
                task_id=task_id,
                user_id=data.user_id,
                role=data.role.value,
                organization_id=self.organization_id,
            )
            self.db.add(record)
            await self.db.flush()
            await self.db.commit()
            await self.db.refresh(record)
            return record
        except IntegrityError as e:
            await self.db.rollback()
            if "unique" in str(e.orig).lower():
                raise ConflictError("User already assigned with this role")
            raise
        except Exception:
            await self.db.rollback()
            raise

    async def delete(self, task_id: UUID, assignment_id: UUID) -> None:
        await self._set_context()
        result = await self.db.execute(
            select(TaskAssignment).where(
                TaskAssignment.id == assignment_id,
                TaskAssignment.task_id == task_id,
                TaskAssignment.organization_id == self.organization_id,
            )
        )
        record = result.scalar_one_or_none()
        if not record:
            raise NotFoundError("TaskAssignment", str(assignment_id))
        try:
            await self.db.delete(record)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/tasks/{task_id}/assignments", tags=["task-assignments"])


def get_repo(db: DatabaseSession, org_id: OrganizationId) -> TaskAssignmentRepository:
    return TaskAssignmentRepository(db, org_id)


@router.get("", response_model=list[TaskAssignmentResponse])
async def list_assignments(
    task_id: UUID,
    repo: TaskAssignmentRepository = Depends(get_repo),
) -> list[TaskAssignment]:
    return await repo.list(task_id)


@router.post(
    "",
    response_model=TaskAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_assignment(
    task_id: UUID,
    data: TaskAssignmentCreate,
    repo: TaskAssignmentRepository = Depends(get_repo),
) -> TaskAssignment:
    return await repo.create(task_id, data)


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(
    task_id: UUID,
    assignment_id: UUID,
    repo: TaskAssignmentRepository = Depends(get_repo),
) -> None:
    await repo.delete(task_id, assignment_id)

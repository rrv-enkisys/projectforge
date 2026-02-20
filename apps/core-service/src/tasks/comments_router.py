"""Router, repository, and schemas for task comments."""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.dependencies import AuthenticatedUser, DatabaseSession, OrganizationId
from ..common.exceptions import NotFoundError, PermissionDeniedError
from ..database import set_organization_context
from .models import Task, TaskComment

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------


class TaskCommentRepository:
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

    async def _get_user_uuid_by_firebase_uid(self, firebase_uid: str) -> UUID:
        from ..users.models import User  # avoid circular import

        result = await self.db.execute(
            select(User.id).where(User.firebase_uid == firebase_uid)
        )
        user_id = result.scalar_one_or_none()
        if not user_id:
            raise NotFoundError("User", firebase_uid)
        return user_id

    async def _get_comment(self, task_id: UUID, comment_id: UUID) -> TaskComment:
        await self._set_context()
        result = await self.db.execute(
            select(TaskComment).where(
                TaskComment.id == comment_id,
                TaskComment.task_id == task_id,
                TaskComment.organization_id == self.organization_id,
            )
        )
        comment = result.scalar_one_or_none()
        if not comment:
            raise NotFoundError("TaskComment", str(comment_id))
        return comment

    async def list(self, task_id: UUID) -> list[TaskComment]:
        await self._get_task(task_id)
        result = await self.db.execute(
            select(TaskComment)
            .where(
                TaskComment.task_id == task_id,
                TaskComment.organization_id == self.organization_id,
            )
            .order_by(TaskComment.created_at.asc())
        )
        return list(result.scalars().all())

    async def create(
        self, task_id: UUID, user_id: UUID, content: str
    ) -> TaskComment:
        await self._get_task(task_id)
        try:
            record = TaskComment(
                task_id=task_id,
                user_id=user_id,
                content=content,
                organization_id=self.organization_id,
            )
            self.db.add(record)
            await self.db.flush()
            await self.db.commit()
            await self.db.refresh(record)
            return record
        except Exception:
            await self.db.rollback()
            raise

    async def update(
        self,
        task_id: UUID,
        comment_id: UUID,
        content: str,
        author_user_id: UUID,
    ) -> TaskComment:
        comment = await self._get_comment(task_id, comment_id)
        if comment.user_id != author_user_id:
            raise PermissionDeniedError(
                "Only the comment author can edit or delete this comment"
            )
        try:
            comment.content = content
            await self.db.flush()
            await self.db.commit()
            await self.db.refresh(comment)
            return comment
        except Exception:
            await self.db.rollback()
            raise

    async def delete(
        self, task_id: UUID, comment_id: UUID, author_user_id: UUID
    ) -> None:
        comment = await self._get_comment(task_id, comment_id)
        if comment.user_id != author_user_id:
            raise PermissionDeniedError(
                "Only the comment author can edit or delete this comment"
            )
        try:
            await self.db.delete(comment)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/tasks/{task_id}/comments", tags=["task-comments"])


def get_repo(db: DatabaseSession, org_id: OrganizationId) -> TaskCommentRepository:
    return TaskCommentRepository(db, org_id)


@router.get("", response_model=list[TaskCommentResponse])
async def list_comments(
    task_id: UUID,
    repo: TaskCommentRepository = Depends(get_repo),
) -> list[TaskComment]:
    return await repo.list(task_id)


@router.post(
    "",
    response_model=TaskCommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    task_id: UUID,
    data: TaskCommentCreate,
    current_user: AuthenticatedUser,
    repo: TaskCommentRepository = Depends(get_repo),
) -> TaskComment:
    user_uuid = await repo._get_user_uuid_by_firebase_uid(current_user.uid)
    return await repo.create(task_id, user_uuid, data.content)


@router.patch("/{comment_id}", response_model=TaskCommentResponse)
async def update_comment(
    task_id: UUID,
    comment_id: UUID,
    data: TaskCommentUpdate,
    current_user: AuthenticatedUser,
    repo: TaskCommentRepository = Depends(get_repo),
) -> TaskComment:
    user_uuid = await repo._get_user_uuid_by_firebase_uid(current_user.uid)
    return await repo.update(task_id, comment_id, data.content, user_uuid)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    task_id: UUID,
    comment_id: UUID,
    current_user: AuthenticatedUser,
    repo: TaskCommentRepository = Depends(get_repo),
) -> None:
    user_uuid = await repo._get_user_uuid_by_firebase_uid(current_user.uid)
    await repo.delete(task_id, comment_id, user_uuid)

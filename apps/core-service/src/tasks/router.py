"""FastAPI router for task endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from ..common.dependencies import DatabaseSession, OrganizationId
from .schemas import TaskCreate, TaskListResponse, TaskResponse, TaskStatusUpdate, TaskUpdate
from .service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_service(db: DatabaseSession, org_id: OrganizationId) -> TaskService:
    """Dependency to get task service."""
    return TaskService(db, org_id)


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    project_id: UUID | None = Query(None, description="Project ID to filter tasks (optional)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: TaskService = Depends(get_service),
) -> TaskListResponse:
    """List all tasks for a project (or all tasks if project_id not provided)."""
    tasks, total = await service.list_tasks(project_id, skip, limit)
    return TaskListResponse(
        data=tasks,
        total=total,
        has_more=(skip + len(tasks)) < total,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    service: TaskService = Depends(get_service),
) -> TaskResponse:
    """Get a specific task by ID."""
    return await service.get_task(task_id)


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    data: TaskCreate,
    service: TaskService = Depends(get_service),
) -> TaskResponse:
    """Create a new task."""
    return await service.create_task(data)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    data: TaskUpdate,
    service: TaskService = Depends(get_service),
) -> TaskResponse:
    """Update an existing task."""
    return await service.update_task(task_id, data)


@router.patch("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: UUID,
    data: TaskStatusUpdate,
    service: TaskService = Depends(get_service),
) -> TaskResponse:
    """Update task status (for Kanban board movements)."""
    return await service.update_status(task_id, data)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    service: TaskService = Depends(get_service),
) -> None:
    """Delete a task."""
    await service.delete_task(task_id)

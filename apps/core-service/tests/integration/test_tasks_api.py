"""Integration tests for Tasks API endpoints."""

from datetime import date, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import (
    create_milestone,
    create_organization,
    create_project,
    create_task,
)


class TestTasksAPI:
    """Tests for Tasks API endpoints."""

    @pytest.fixture(autouse=True)
    async def setup(self, db_with_org_context: AsyncSession, test_org_id: UUID) -> None:
        """Setup test data."""
        self.db = db_with_org_context
        self.org_id = test_org_id

        # Create organization and project
        org = create_organization(organization_id=test_org_id)
        self.db.add(org)

        self.project = create_project(organization_id=test_org_id, name="Test Project")
        self.db.add(self.project)
        await self.db.flush()

    async def test_create_task(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test creating a new task."""
        task_data = {
            "title": "New Task",
            "description": "Task description",
            "project_id": str(self.project.id),
            "status": "todo",
            "priority": "high",
            "due_date": str(date.today() + timedelta(days=7)),
        }

        response = client.post("/api/v1/tasks", json=task_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == task_data["title"]
        assert data["project_id"] == task_data["project_id"]
        assert "id" in data

    async def test_create_task_with_milestone(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test creating task with milestone."""
        # Create milestone
        milestone = create_milestone(
            organization_id=self.org_id, project_id=self.project.id
        )
        self.db.add(milestone)
        await self.db.flush()

        task_data = {
            "title": "Task with Milestone",
            "project_id": str(self.project.id),
            "milestone_id": str(milestone.id),
        }

        response = client.post("/api/v1/tasks", json=task_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["milestone_id"] == str(milestone.id)

    async def test_create_task_invalid_milestone(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test creating task with milestone from different project."""
        # Create another project and milestone
        other_project = create_project(organization_id=self.org_id, name="Other Project")
        self.db.add(other_project)
        await self.db.flush()

        other_milestone = create_milestone(
            organization_id=self.org_id, project_id=other_project.id
        )
        self.db.add(other_milestone)
        await self.db.flush()

        task_data = {
            "title": "Invalid Task",
            "project_id": str(self.project.id),
            "milestone_id": str(other_milestone.id),  # Wrong project
        }

        response = client.post("/api/v1/tasks", json=task_data, headers=auth_headers)

        assert response.status_code == 422
        error = response.json()
        assert "same project" in error["error"]["message"]

    async def test_update_task_status_transition(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test task status transition validation."""
        from src.tasks.models import TaskStatus

        # Create task in DONE state
        task = create_task(
            organization_id=self.org_id,
            project_id=self.project.id,
            status=TaskStatus.DONE,
        )
        self.db.add(task)
        await self.db.flush()

        # Try invalid transition from DONE to TODO
        update_data = {"status": "todo"}

        response = client.patch(
            f"/api/v1/tasks/{task.id}", json=update_data, headers=auth_headers
        )

        assert response.status_code == 422
        error = response.json()
        assert "Cannot transition" in error["error"]["message"]

    async def test_bulk_create_tasks(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test bulk task creation."""
        tasks_data = {
            "tasks": [
                {
                    "title": f"Bulk Task {i}",
                    "project_id": str(self.project.id),
                    "priority": "medium",
                }
                for i in range(5)
            ]
        }

        response = client.post("/api/v1/tasks/bulk", json=tasks_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert len(data) == 5
        assert all(task["title"].startswith("Bulk Task") for task in data)

    async def test_bulk_update_tasks(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test bulk task update."""
        # Create tasks
        task_ids = []
        for i in range(3):
            task = create_task(organization_id=self.org_id, project_id=self.project.id)
            self.db.add(task)
            await self.db.flush()
            task_ids.append(str(task.id))

        update_data = {
            "task_ids": task_ids,
            "update": {"priority": "critical"},
        }

        response = client.patch("/api/v1/tasks/bulk", json=update_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["updated"] == 3

    async def test_bulk_delete_tasks(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test bulk task deletion."""
        # Create tasks
        task_ids = []
        for i in range(3):
            task = create_task(organization_id=self.org_id, project_id=self.project.id)
            self.db.add(task)
            await self.db.flush()
            task_ids.append(str(task.id))

        delete_data = {"task_ids": task_ids}

        response = client.delete("/api/v1/tasks/bulk", json=delete_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["deleted"] == 3

    async def test_search_tasks_with_filters(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test task search with filters."""
        from src.tasks.models import TaskPriority, TaskStatus

        # Create tasks with different statuses and priorities
        task1 = create_task(
            organization_id=self.org_id,
            project_id=self.project.id,
            title="High Priority Task",
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH,
        )
        task2 = create_task(
            organization_id=self.org_id,
            project_id=self.project.id,
            title="Medium Priority Task",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.MEDIUM,
        )
        self.db.add_all([task1, task2])
        await self.db.flush()

        # Search for high priority tasks
        search_data = {
            "project_id": str(self.project.id),
            "priority": ["high"],
        }

        response = client.post("/api/v1/tasks/search", json=search_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert all(task["priority"] == "high" for task in data["data"])

    async def test_search_tasks_with_text_search(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test task search with text search."""
        # Create tasks
        task1 = create_task(
            organization_id=self.org_id,
            project_id=self.project.id,
            title="Implement authentication",
        )
        task2 = create_task(
            organization_id=self.org_id,
            project_id=self.project.id,
            title="Add tests",
        )
        self.db.add_all([task1, task2])
        await self.db.flush()

        # Search for "authentication"
        search_data = {"search": "authentication"}

        response = client.post("/api/v1/tasks/search", json=search_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any("authentication" in task["title"].lower() for task in data["data"])

    async def test_search_tasks_with_sorting(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test task search with custom sorting."""
        # Create tasks with different due dates
        for i in range(3):
            task = create_task(
                organization_id=self.org_id,
                project_id=self.project.id,
                due_date=date.today() + timedelta(days=i),
            )
            self.db.add(task)
        await self.db.flush()

        # Search with sorting by due_date descending
        search_data = {
            "project_id": str(self.project.id),
        }
        sort_data = {"field": "due_date", "direction": "desc"}

        response = client.post(
            "/api/v1/tasks/search",
            json={"filters": search_data, "sort": sort_data},
            headers=auth_headers,
        )

        assert response.status_code == 200

    async def test_list_tasks_by_project(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test listing tasks filtered by project."""
        # Create tasks
        for i in range(3):
            task = create_task(organization_id=self.org_id, project_id=self.project.id)
            self.db.add(task)
        await self.db.flush()

        response = client.get(
            f"/api/v1/tasks?project_id={self.project.id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3

    async def test_task_circular_dependency_prevention(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test prevention of circular dependencies in task hierarchy."""
        # Create parent and child tasks
        parent_task = create_task(
            organization_id=self.org_id, project_id=self.project.id, title="Parent"
        )
        self.db.add(parent_task)
        await self.db.flush()

        child_task = create_task(
            organization_id=self.org_id,
            project_id=self.project.id,
            title="Child",
            parent_task_id=parent_task.id,
        )
        self.db.add(child_task)
        await self.db.flush()

        # Try to make parent a child of child (circular)
        update_data = {"parent_task_id": str(child_task.id)}

        response = client.patch(
            f"/api/v1/tasks/{parent_task.id}", json=update_data, headers=auth_headers
        )

        assert response.status_code == 422
        error = response.json()
        assert "Circular dependency" in error["error"]["message"]

"""Integration tests for Projects API endpoints."""

from datetime import date, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import create_organization, create_project


class TestProjectsAPI:
    """Tests for Projects API endpoints."""

    @pytest.fixture(autouse=True)
    async def setup(self, db_with_org_context: AsyncSession, test_org_id: UUID) -> None:
        """Setup test data."""
        self.db = db_with_org_context
        self.org_id = test_org_id

        # Create organization
        org = create_organization(organization_id=test_org_id)
        self.db.add(org)
        await self.db.flush()

    async def test_create_project(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test creating a new project."""
        project_data = {
            "name": "New Project",
            "description": "Project description",
            "status": "planning",
            "start_date": str(date.today()),
            "end_date": str(date.today() + timedelta(days=30)),
            "budget": 50000.0,
        }

        response = client.post("/api/v1/projects", json=project_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == project_data["name"]
        assert data["description"] == project_data["description"]
        assert data["status"] == project_data["status"]
        assert "id" in data
        assert data["organization_id"] == str(self.org_id)

    async def test_create_project_invalid_date_range(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test creating project with invalid date range."""
        project_data = {
            "name": "Invalid Project",
            "start_date": str(date.today() + timedelta(days=30)),
            "end_date": str(date.today()),  # End before start
        }

        response = client.post("/api/v1/projects", json=project_data, headers=auth_headers)

        assert response.status_code == 422
        error = response.json()
        assert "error" in error

    async def test_create_project_negative_budget(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test creating project with negative budget."""
        project_data = {
            "name": "Invalid Budget Project",
            "budget": -1000.0,
        }

        response = client.post("/api/v1/projects", json=project_data, headers=auth_headers)

        assert response.status_code == 422

    async def test_list_projects(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test listing projects."""
        # Create test projects
        for i in range(3):
            project = create_project(
                organization_id=self.org_id,
                name=f"Project {i}",
            )
            self.db.add(project)
        await self.db.flush()

        response = client.get("/api/v1/projects", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert data["total"] >= 3
        assert len(data["data"]) >= 3

    async def test_get_project(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test getting a specific project."""
        # Create project
        project = create_project(organization_id=self.org_id, name="Test Project")
        self.db.add(project)
        await self.db.flush()

        response = client.get(f"/api/v1/projects/{project.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(project.id)
        assert data["name"] == project.name

    async def test_get_project_not_found(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test getting non-existent project."""
        fake_id = uuid4()
        response = client.get(f"/api/v1/projects/{fake_id}", headers=auth_headers)

        assert response.status_code == 404

    async def test_update_project(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test updating a project."""
        # Create project
        project = create_project(organization_id=self.org_id, name="Original Name")
        self.db.add(project)
        await self.db.flush()

        update_data = {
            "name": "Updated Name",
            "description": "Updated description",
        }

        response = client.patch(
            f"/api/v1/projects/{project.id}", json=update_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]

    async def test_update_project_invalid_status_transition(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test updating project with invalid status transition."""
        # Create completed project
        from src.projects.models import ProjectStatus

        project = create_project(
            organization_id=self.org_id,
            name="Completed Project",
            status=ProjectStatus.COMPLETED,
        )
        self.db.add(project)
        await self.db.flush()

        update_data = {"status": "active"}  # Cannot go from completed to active

        response = client.patch(
            f"/api/v1/projects/{project.id}", json=update_data, headers=auth_headers
        )

        assert response.status_code == 422
        error = response.json()
        assert "Cannot transition" in error["error"]["message"]

    async def test_delete_project(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test deleting a project."""
        # Create project
        project = create_project(organization_id=self.org_id)
        self.db.add(project)
        await self.db.flush()

        response = client.delete(f"/api/v1/projects/{project.id}", headers=auth_headers)

        assert response.status_code == 204

        # Verify deletion
        get_response = client.get(f"/api/v1/projects/{project.id}", headers=auth_headers)
        assert get_response.status_code == 404

    async def test_get_project_statistics(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test getting project statistics."""
        from tests.factories import create_milestone, create_task

        # Create project
        project = create_project(organization_id=self.org_id)
        self.db.add(project)
        await self.db.flush()

        # Create some tasks and milestones
        for i in range(5):
            task = create_task(organization_id=self.org_id, project_id=project.id)
            self.db.add(task)

        milestone = create_milestone(organization_id=self.org_id, project_id=project.id)
        self.db.add(milestone)
        await self.db.flush()

        response = client.get(
            f"/api/v1/projects/{project.id}/statistics", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == str(project.id)
        assert data["total_tasks"] >= 5
        assert data["total_milestones"] >= 1
        assert "tasks_by_status" in data
        assert "tasks_by_priority" in data
        assert "completion_percentage" in data

    async def test_list_projects_pagination(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test project list pagination."""
        # Create 15 projects
        for i in range(15):
            project = create_project(organization_id=self.org_id, name=f"Project {i}")
            self.db.add(project)
        await self.db.flush()

        # Get first page
        response = client.get("/api/v1/projects?skip=0&limit=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 10
        assert data["has_more"] is True

        # Get second page
        response = client.get("/api/v1/projects?skip=10&limit=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) >= 5

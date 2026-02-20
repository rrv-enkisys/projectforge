"""Integration tests for task dependencies, assignments, and comments APIs."""
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import (
    create_organization,
    create_project,
    create_task,
    create_user,
    create_user_organization,
)


class TestTaskDependenciesAPI:
    """Tests for GET/POST/DELETE /api/v1/tasks/{task_id}/dependencies."""

    @pytest.fixture(autouse=True)
    async def setup(self, db_with_org_context: AsyncSession, test_org_id: UUID) -> None:
        self.db = db_with_org_context
        self.org_id = test_org_id

        org = create_organization(organization_id=test_org_id)
        self.db.add(org)

        self.project = create_project(organization_id=test_org_id)
        self.db.add(self.project)

        self.task_a = create_task(
            organization_id=test_org_id,
            project_id=self.project.id,
            title="Task A",
        )
        self.task_b = create_task(
            organization_id=test_org_id,
            project_id=self.project.id,
            title="Task B",
        )
        self.db.add(self.task_a)
        self.db.add(self.task_b)
        await self.db.flush()

    async def test_list_dependencies_empty(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """GET returns empty list when no dependencies."""
        response = client.get(
            f"/api/v1/tasks/{self.task_a.id}/dependencies",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json() == []

    async def test_create_dependency(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """POST creates a finish_to_start dependency."""
        response = client.post(
            f"/api/v1/tasks/{self.task_a.id}/dependencies",
            json={
                "depends_on_id": str(self.task_b.id),
                "dependency_type": "finish_to_start",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["task_id"] == str(self.task_a.id)
        assert data["depends_on_id"] == str(self.task_b.id)
        assert data["dependency_type"] == "finish_to_start"
        assert "id" in data

    async def test_create_duplicate_dependency_returns_409(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """POST with duplicate (task_id, depends_on_id) returns 409."""
        payload = {
            "depends_on_id": str(self.task_b.id),
            "dependency_type": "finish_to_start",
        }
        client.post(
            f"/api/v1/tasks/{self.task_a.id}/dependencies",
            json=payload,
            headers=auth_headers,
        )
        response = client.post(
            f"/api/v1/tasks/{self.task_a.id}/dependencies",
            json=payload,
            headers=auth_headers,
        )
        assert response.status_code == 409

    async def test_create_circular_dependency_returns_422(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """POST that would create a cycle returns 422 with circular_dependency rule."""
        # A depends on B
        client.post(
            f"/api/v1/tasks/{self.task_a.id}/dependencies",
            json={"depends_on_id": str(self.task_b.id)},
            headers=auth_headers,
        )
        # B depends on A → cycle
        response = client.post(
            f"/api/v1/tasks/{self.task_b.id}/dependencies",
            json={"depends_on_id": str(self.task_a.id)},
            headers=auth_headers,
        )
        assert response.status_code == 422
        assert response.json()["error"]["rule"] == "circular_dependency"

    async def test_delete_dependency(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """DELETE removes a dependency and returns 204."""
        create_resp = client.post(
            f"/api/v1/tasks/{self.task_a.id}/dependencies",
            json={"depends_on_id": str(self.task_b.id)},
            headers=auth_headers,
        )
        dep_id = create_resp.json()["id"]

        delete_resp = client.delete(
            f"/api/v1/tasks/{self.task_a.id}/dependencies/{dep_id}",
            headers=auth_headers,
        )
        assert delete_resp.status_code == 204

    async def test_delete_nonexistent_returns_404(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.delete(
            f"/api/v1/tasks/{self.task_a.id}/dependencies/{uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_cross_project_dependency_returns_422(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Tasks from different projects cannot have dependencies."""
        other_project = create_project(
            organization_id=self.org_id, name="Other Project"
        )
        self.db.add(other_project)
        other_task = create_task(
            organization_id=self.org_id,
            project_id=other_project.id,
            title="Other Task",
        )
        self.db.add(other_task)
        await self.db.flush()

        response = client.post(
            f"/api/v1/tasks/{self.task_a.id}/dependencies",
            json={"depends_on_id": str(other_task.id)},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestTaskAssignmentsAPI:
    """Tests for GET/POST/DELETE /api/v1/tasks/{task_id}/assignments."""

    @pytest.fixture(autouse=True)
    async def setup(self, db_with_org_context: AsyncSession, test_org_id: UUID) -> None:
        self.db = db_with_org_context
        self.org_id = test_org_id

        org = create_organization(organization_id=test_org_id)
        self.db.add(org)

        self.project = create_project(organization_id=test_org_id)
        self.db.add(self.project)

        self.task = create_task(
            organization_id=test_org_id, project_id=self.project.id
        )
        self.db.add(self.task)

        self.user = create_user(firebase_uid="test-firebase-uid")
        self.db.add(self.user)

        user_org = create_user_organization(
            user_id=self.user.id, organization_id=test_org_id
        )
        self.db.add(user_org)

        await self.db.flush()

    async def test_list_assignments_empty(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get(
            f"/api/v1/tasks/{self.task.id}/assignments",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json() == []

    async def test_create_assignment(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.post(
            f"/api/v1/tasks/{self.task.id}/assignments",
            json={"user_id": str(self.user.id), "role": "responsible"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["task_id"] == str(self.task.id)
        assert data["user_id"] == str(self.user.id)
        assert data["role"] == "responsible"

    async def test_create_duplicate_assignment_returns_409(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        payload = {"user_id": str(self.user.id), "role": "responsible"}
        client.post(
            f"/api/v1/tasks/{self.task.id}/assignments",
            json=payload,
            headers=auth_headers,
        )
        response = client.post(
            f"/api/v1/tasks/{self.task.id}/assignments",
            json=payload,
            headers=auth_headers,
        )
        assert response.status_code == 409

    async def test_assign_nonexistent_user_returns_404(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.post(
            f"/api/v1/tasks/{self.task.id}/assignments",
            json={"user_id": str(uuid4()), "role": "responsible"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_delete_assignment(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        create_resp = client.post(
            f"/api/v1/tasks/{self.task.id}/assignments",
            json={"user_id": str(self.user.id), "role": "responsible"},
            headers=auth_headers,
        )
        assignment_id = create_resp.json()["id"]

        delete_resp = client.delete(
            f"/api/v1/tasks/{self.task.id}/assignments/{assignment_id}",
            headers=auth_headers,
        )
        assert delete_resp.status_code == 204


class TestTaskCommentsAPI:
    """Tests for GET/POST/PATCH/DELETE /api/v1/tasks/{task_id}/comments."""

    @pytest.fixture(autouse=True)
    async def setup(self, db_with_org_context: AsyncSession, test_org_id: UUID) -> None:
        self.db = db_with_org_context
        self.org_id = test_org_id

        org = create_organization(organization_id=test_org_id)
        self.db.add(org)

        self.project = create_project(organization_id=test_org_id)
        self.db.add(self.project)

        self.task = create_task(
            organization_id=test_org_id, project_id=self.project.id
        )
        self.db.add(self.task)

        # In debug mode, the current user is "ricardo-firebase-uid"
        self.user = create_user(firebase_uid="ricardo-firebase-uid")
        self.db.add(self.user)

        await self.db.flush()

    async def test_list_comments_empty(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get(
            f"/api/v1/tasks/{self.task.id}/comments",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json() == []

    async def test_create_comment(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.post(
            f"/api/v1/tasks/{self.task.id}/comments",
            json={"content": "This is a test comment"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "This is a test comment"
        assert data["task_id"] == str(self.task.id)
        assert "id" in data

    async def test_create_comment_empty_content_returns_422(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.post(
            f"/api/v1/tasks/{self.task.id}/comments",
            json={"content": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_update_comment(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        create_resp = client.post(
            f"/api/v1/tasks/{self.task.id}/comments",
            json={"content": "Original content"},
            headers=auth_headers,
        )
        comment_id = create_resp.json()["id"]

        update_resp = client.patch(
            f"/api/v1/tasks/{self.task.id}/comments/{comment_id}",
            json={"content": "Updated content"},
            headers=auth_headers,
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["content"] == "Updated content"

    async def test_delete_comment(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        create_resp = client.post(
            f"/api/v1/tasks/{self.task.id}/comments",
            json={"content": "To be deleted"},
            headers=auth_headers,
        )
        comment_id = create_resp.json()["id"]

        delete_resp = client.delete(
            f"/api/v1/tasks/{self.task.id}/comments/{comment_id}",
            headers=auth_headers,
        )
        assert delete_resp.status_code == 204

    async def test_list_comments_ordered_by_created_at(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Comments are returned in ascending chronological order."""
        for i in range(3):
            client.post(
                f"/api/v1/tasks/{self.task.id}/comments",
                json={"content": f"Comment {i}"},
                headers=auth_headers,
            )

        response = client.get(
            f"/api/v1/tasks/{self.task.id}/comments",
            headers=auth_headers,
        )
        assert response.status_code == 200
        comments = response.json()
        assert len(comments) == 3
        # Verify ascending order
        for i in range(len(comments) - 1):
            assert comments[i]["created_at"] <= comments[i + 1]["created_at"]

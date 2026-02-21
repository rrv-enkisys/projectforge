from __future__ import annotations

"""Repository for fetching real project data for copilot analysis."""
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ProjectDataRepository:
    """Fetches project data from the shared PostgreSQL database."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_project_data(
        self,
        project_id: UUID,
        organization_id: UUID,
    ) -> dict:
        """
        Fetch complete project data including tasks and milestones.

        Returns a unified dict for copilot analysis.
        """
        project = await self._get_project(project_id, organization_id)
        if not project:
            return {}

        tasks = await self._get_tasks(project_id, organization_id)
        milestones = await self._get_milestones(project_id, organization_id)

        return {
            "id": str(project["id"]),
            "name": project["name"],
            "description": project.get("description"),
            "status": project.get("status"),
            "start_date": project["start_date"].isoformat() if project.get("start_date") else None,
            "end_date": project["end_date"].isoformat() if project.get("end_date") else None,
            "budget": float(project["budget"]) if project.get("budget") else None,
            "organization_id": str(organization_id),
            "tasks": tasks,
            "milestones": milestones,
        }

    async def _get_project(
        self,
        project_id: UUID,
        organization_id: UUID,
    ) -> dict | None:
        """Fetch project metadata."""
        try:
            result = await self.db.execute(
                text(
                    """
                    SELECT id, name, description, status, start_date, end_date, budget
                    FROM projects
                    WHERE id = :project_id
                      AND organization_id = :org_id
                """
                ),
                {"project_id": str(project_id), "org_id": str(organization_id)},
            )
            row = result.mappings().fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.warning(f"Could not fetch project {project_id}: {e}")
            return None

    async def _get_tasks(
        self,
        project_id: UUID,
        organization_id: UUID,
    ) -> list[dict]:
        """Fetch tasks for a project."""
        try:
            result = await self.db.execute(
                text(
                    """
                    SELECT id, title, description, status, priority,
                           due_date, start_date, estimated_hours, actual_hours,
                           updated_at, created_at
                    FROM tasks
                    WHERE project_id = :project_id
                      AND organization_id = :org_id
                    ORDER BY created_at DESC
                """
                ),
                {"project_id": str(project_id), "org_id": str(organization_id)},
            )
            rows = result.mappings().fetchall()
            return [
                {
                    "id": str(r["id"]),
                    "title": r["title"],
                    "description": r.get("description"),
                    "status": r["status"],
                    "priority": r["priority"],
                    "due_date": r["due_date"].isoformat() if r.get("due_date") else None,
                    "start_date": r["start_date"].isoformat() if r.get("start_date") else None,
                    "estimated_hours": float(r["estimated_hours"]) if r.get("estimated_hours") else None,
                    "actual_hours": float(r["actual_hours"]) if r.get("actual_hours") else None,
                    "updated_at": r["updated_at"].isoformat() if r.get("updated_at") else None,
                    "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
                }
                for r in rows
            ]
        except Exception as e:
            logger.warning(f"Could not fetch tasks for project {project_id}: {e}")
            return []

    async def _get_milestones(
        self,
        project_id: UUID,
        organization_id: UUID,
    ) -> list[dict]:
        """Fetch milestones for a project."""
        try:
            result = await self.db.execute(
                text(
                    """
                    SELECT id, name, description, status, target_date
                    FROM milestones
                    WHERE project_id = :project_id
                      AND organization_id = :org_id
                    ORDER BY target_date ASC NULLS LAST
                """
                ),
                {"project_id": str(project_id), "org_id": str(organization_id)},
            )
            rows = result.mappings().fetchall()
            return [
                {
                    "id": str(r["id"]),
                    "title": r["name"],
                    "description": r.get("description"),
                    "status": r["status"],
                    "target_date": r["target_date"].isoformat() if r.get("target_date") else None,
                    "is_completed": r["status"] == "completed",
                }
                for r in rows
            ]
        except Exception as e:
            logger.warning(f"Could not fetch milestones for project {project_id}: {e}")
            return []

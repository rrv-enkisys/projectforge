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
            "client_name": project.get("client_name"),
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
                    SELECT
                        p.id, p.name, p.description, p.status,
                        p.start_date, p.end_date, p.budget,
                        c.name AS client_name
                    FROM projects p
                    LEFT JOIN clients c ON p.client_id = c.id
                    WHERE p.id = :project_id
                      AND p.organization_id = :org_id
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
                    SELECT
                        t.id, t.title, t.description, t.status, t.priority,
                        t.start_date, t.due_date, t.estimated_hours, t.actual_hours,
                        t.updated_at, t.created_at,
                        COALESCE(
                            json_agg(
                                json_build_object(
                                    'user_id', u.id,
                                    'name', u.name,
                                    'email', u.email
                                )
                            ) FILTER (WHERE u.id IS NOT NULL),
                            '[]'
                        ) AS assignees
                    FROM tasks t
                    LEFT JOIN task_assignments ta ON t.id = ta.task_id
                    LEFT JOIN users u ON ta.user_id = u.id
                    WHERE t.project_id = :project_id
                      AND t.organization_id = :org_id
                    GROUP BY t.id
                    ORDER BY t.due_date ASC NULLS LAST
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
                    "assignees": r["assignees"] if isinstance(r["assignees"], list) else [],
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

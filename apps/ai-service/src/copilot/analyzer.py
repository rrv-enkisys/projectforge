from __future__ import annotations

"""Project analysis utilities"""
import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


class ProjectAnalyzer:
    """Analyzes project data to extract insights"""

    def analyze_project_health(self, project_data: dict) -> dict:
        """
        Analyze overall project health

        Args:
            project_data: Project data including tasks, milestones, etc.

        Returns:
            Health analysis dictionary
        """
        health_score = 100
        issues = []

        # Analyze task completion rate
        tasks = project_data.get("tasks", [])
        if tasks:
            completed_tasks = [t for t in tasks if t.get("status") in ("done", "completed")]
            completion_rate = len(completed_tasks) / len(tasks)

            if completion_rate < 0.3:
                health_score -= 20
                issues.append("Low task completion rate")

        # Analyze overdue items
        now = datetime.now(timezone.utc)
        now_naive = now.replace(tzinfo=None)

        def parse_date(s: str) -> datetime:
            """Parse ISO date string; returns naive datetime for comparison."""
            dt = datetime.fromisoformat(s)
            return dt.replace(tzinfo=None) if dt.tzinfo else dt

        overdue_tasks = [
            t for t in tasks
            if t.get("due_date") and parse_date(t["due_date"]) < now_naive
            and t.get("status") not in ("done", "completed")
        ]

        if overdue_tasks:
            health_score -= 15 * min(len(overdue_tasks), 3)
            issues.append(f"{len(overdue_tasks)} overdue tasks")

        # Analyze milestones
        milestones = project_data.get("milestones", [])
        overdue_milestones = [
            m for m in milestones
            if m.get("target_date") and parse_date(m["target_date"]) < now_naive
            and not m.get("is_completed")
        ]

        if overdue_milestones:
            health_score -= 20
            issues.append(f"{len(overdue_milestones)} overdue milestones")

        # Determine health status
        if health_score >= 80:
            status = "healthy"
        elif health_score >= 60:
            status = "at_risk"
        else:
            status = "critical"

        completed_count = len([t for t in tasks if t.get("status") in ("done", "completed")])
        return {
            "score": max(0, health_score),
            "status": status,
            "issues": issues,
            "total_tasks": len(tasks),
            "completed_tasks": completed_count,
            "task_completion_rate": completion_rate if tasks else 0,
            "overdue_tasks_count": len(overdue_tasks),
            "overdue_milestones_count": len(overdue_milestones)
        }

    def detect_risks(self, project_data: dict) -> list[dict]:
        """
        Detect potential project risks

        Args:
            project_data: Project data

        Returns:
            List of detected risks
        """
        risks = []

        tasks = project_data.get("tasks", [])
        milestones = project_data.get("milestones", [])
        now = datetime.now(timezone.utc)
        now_naive = now.replace(tzinfo=None)

        def parse_date(s: str) -> datetime:
            dt = datetime.fromisoformat(s)
            return dt.replace(tzinfo=None) if dt.tzinfo else dt

        # Risk: Too many overdue tasks
        overdue_count = sum(
            1 for t in tasks
            if t.get("due_date") and parse_date(t["due_date"]) < now_naive
            and t.get("status") not in ("done", "completed")
        )

        if overdue_count > 5:
            risks.append({
                "type": "overdue_tasks",
                "severity": "high",
                "description": f"{overdue_count} tasks are overdue",
                "impact": "Project timeline may be compromised",
                "mitigation": "Review and reprioritize tasks, consider extending deadline"
            })

        # Risk: No recent activity
        if tasks:
            latest_task_update = max(
                (parse_date(t["updated_at"]) for t in tasks if t.get("updated_at")),
                default=None
            )

            if latest_task_update:
                days_since_update = (now_naive - latest_task_update).days
                if days_since_update > 7:
                    risks.append({
                        "type": "low_activity",
                        "severity": "medium",
                        "description": f"No task updates in {days_since_update} days",
                        "impact": "Project may be stalled or lacking attention",
                        "mitigation": "Check team availability and blockers"
                    })

        # Risk: Milestone approaching without completion
        for milestone in milestones:
            if milestone.get("target_date") and not milestone.get("is_completed"):
                target = parse_date(milestone["target_date"])
                days_until = (target - now_naive).days

                if 0 < days_until <= 7:
                    risks.append({
                        "type": "milestone_deadline",
                        "severity": "high",
                        "description": f"Milestone '{milestone.get('title')}' due in {days_until} days",
                        "impact": "Critical deadline approaching",
                        "mitigation": "Focus resources on milestone tasks"
                    })

        # Risk: High task concentration on one person
        task_assignees = [t.get("assignee_id") for t in tasks if t.get("assignee_id")]
        if task_assignees:
            from collections import Counter
            assignee_counts = Counter(task_assignees)
            max_count = max(assignee_counts.values())

            if max_count > len(tasks) * 0.6:  # One person has >60% of tasks
                risks.append({
                    "type": "resource_bottleneck",
                    "severity": "medium",
                    "description": "Tasks heavily concentrated on one team member",
                    "impact": "Single point of failure, potential burnout",
                    "mitigation": "Redistribute tasks across team members"
                })

        return risks

    def predict_completion(self, project_data: dict) -> dict:
        """
        Predict project completion timeline

        Args:
            project_data: Project data

        Returns:
            Completion prediction
        """
        tasks = project_data.get("tasks", [])
        if not tasks:
            return {
                "predicted_date": None,
                "confidence": "low",
                "reasoning": "No tasks to analyze"
            }

        # Calculate completion velocity
        completed_tasks = [t for t in tasks if t.get("status") in ("done", "completed")]
        if not completed_tasks:
            return {
                "predicted_date": None,
                "confidence": "low",
                "reasoning": "No completed tasks to establish velocity"
            }

        # Simple prediction based on completion rate
        completion_rate = len(completed_tasks) / len(tasks)
        remaining_tasks = len(tasks) - len(completed_tasks)

        # Estimate days per task based on completed tasks
        # This is simplified - real implementation would use actual timestamps
        avg_days_per_task = 3  # Placeholder

        estimated_days = remaining_tasks * avg_days_per_task
        predicted_date = datetime.now(timezone.utc).replace(microsecond=0)

        from datetime import timedelta
        predicted_date += timedelta(days=estimated_days)

        confidence = "high" if completion_rate > 0.5 else "medium" if completion_rate > 0.2 else "low"

        return {
            "predicted_date": predicted_date.isoformat(),
            "confidence": confidence,
            "estimated_days_remaining": estimated_days,
            "completion_rate": completion_rate,
            "reasoning": f"Based on {len(completed_tasks)} completed tasks out of {len(tasks)}"
        }

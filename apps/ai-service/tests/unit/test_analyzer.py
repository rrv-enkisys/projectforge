"""Unit tests for ProjectAnalyzer."""
from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from src.copilot.analyzer import ProjectAnalyzer


@pytest.fixture
def analyzer() -> ProjectAnalyzer:
    return ProjectAnalyzer()


@pytest.fixture
def empty_project() -> dict:
    return {"id": str(uuid4()), "tasks": [], "milestones": []}


@pytest.fixture
def healthy_project() -> dict:
    now = datetime.utcnow()
    return {
        "id": str(uuid4()),
        "tasks": [
            {"id": str(uuid4()), "status": "done", "priority": "high",
             "due_date": (now + timedelta(days=5)).isoformat(),
             "updated_at": now.isoformat(), "assignee_id": str(uuid4())},
            {"id": str(uuid4()), "status": "done", "priority": "medium",
             "due_date": (now + timedelta(days=10)).isoformat(),
             "updated_at": now.isoformat(), "assignee_id": str(uuid4())},
            {"id": str(uuid4()), "status": "in_progress", "priority": "low",
             "due_date": (now + timedelta(days=20)).isoformat(),
             "updated_at": now.isoformat(), "assignee_id": str(uuid4())},
        ],
        "milestones": [
            {"id": str(uuid4()), "title": "M1", "is_completed": True,
             "target_date": (now - timedelta(days=5)).isoformat()},
        ],
    }


@pytest.fixture
def critical_project() -> dict:
    now = datetime.utcnow()
    return {
        "id": str(uuid4()),
        "tasks": [
            {"id": str(uuid4()), "status": "todo", "priority": "high",
             "due_date": (now - timedelta(days=10)).isoformat(),
             "updated_at": (now - timedelta(days=20)).isoformat(), "assignee_id": str(uuid4())},
            {"id": str(uuid4()), "status": "todo", "priority": "high",
             "due_date": (now - timedelta(days=8)).isoformat(),
             "updated_at": (now - timedelta(days=20)).isoformat(), "assignee_id": str(uuid4())},
            {"id": str(uuid4()), "status": "todo", "priority": "medium",
             "due_date": (now - timedelta(days=5)).isoformat(),
             "updated_at": (now - timedelta(days=20)).isoformat(), "assignee_id": str(uuid4())},
            {"id": str(uuid4()), "status": "todo", "priority": "low",
             "due_date": (now - timedelta(days=3)).isoformat(),
             "updated_at": (now - timedelta(days=20)).isoformat(), "assignee_id": str(uuid4())},
            {"id": str(uuid4()), "status": "todo", "priority": "low",
             "due_date": (now - timedelta(days=1)).isoformat(),
             "updated_at": (now - timedelta(days=20)).isoformat(), "assignee_id": str(uuid4())},
            {"id": str(uuid4()), "status": "todo", "priority": "low",
             "due_date": (now - timedelta(days=1)).isoformat(),
             "updated_at": (now - timedelta(days=20)).isoformat(), "assignee_id": str(uuid4())},
        ],
        "milestones": [
            {"id": str(uuid4()), "title": "Critical M", "is_completed": False,
             "target_date": (now - timedelta(days=5)).isoformat()},
        ],
    }


class TestAnalyzeProjectHealth:
    def test_empty_project_returns_healthy(self, analyzer: ProjectAnalyzer, empty_project: dict) -> None:
        result = analyzer.analyze_project_health(empty_project)
        assert result["score"] == 100
        assert result["status"] == "healthy"
        assert result["issues"] == []
        assert result["task_completion_rate"] == 0

    def test_healthy_project_high_score(self, analyzer: ProjectAnalyzer, healthy_project: dict) -> None:
        result = analyzer.analyze_project_health(healthy_project)
        assert result["score"] >= 80
        assert result["status"] == "healthy"
        assert result["overdue_tasks_count"] == 0

    def test_critical_project_low_score(self, analyzer: ProjectAnalyzer, critical_project: dict) -> None:
        result = analyzer.analyze_project_health(critical_project)
        assert result["score"] < 60
        assert result["status"] == "critical"
        assert result["overdue_tasks_count"] > 0
        assert len(result["issues"]) > 0

    def test_overdue_tasks_reduce_score(self, analyzer: ProjectAnalyzer, critical_project: dict) -> None:
        result = analyzer.analyze_project_health(critical_project)
        assert result["overdue_tasks_count"] == 6

    def test_overdue_milestone_reduces_score(self, analyzer: ProjectAnalyzer, critical_project: dict) -> None:
        result = analyzer.analyze_project_health(critical_project)
        assert result["overdue_milestones_count"] == 1
        assert "overdue milestones" in str(result["issues"])

    def test_completion_rate_calculated_correctly(self, analyzer: ProjectAnalyzer, healthy_project: dict) -> None:
        result = analyzer.analyze_project_health(healthy_project)
        # 2 out of 3 tasks are done
        assert abs(result["task_completion_rate"] - 2 / 3) < 0.01

    def test_score_never_below_zero(self, analyzer: ProjectAnalyzer, critical_project: dict) -> None:
        result = analyzer.analyze_project_health(critical_project)
        assert result["score"] >= 0


class TestDetectRisks:
    def test_no_risks_on_empty_project(self, analyzer: ProjectAnalyzer, empty_project: dict) -> None:
        risks = analyzer.detect_risks(empty_project)
        assert isinstance(risks, list)

    def test_detects_overdue_tasks_risk(self, analyzer: ProjectAnalyzer, critical_project: dict) -> None:
        risks = analyzer.detect_risks(critical_project)
        risk_types = [r["type"] for r in risks]
        assert "overdue_tasks" in risk_types

    def test_detects_low_activity_risk(self, analyzer: ProjectAnalyzer) -> None:
        now = datetime.utcnow()
        stale_project = {
            "tasks": [
                {"id": str(uuid4()), "status": "todo", "due_date": None,
                 "updated_at": (now - timedelta(days=10)).isoformat(), "assignee_id": None},
            ],
            "milestones": [],
        }
        risks = analyzer.detect_risks(stale_project)
        risk_types = [r["type"] for r in risks]
        assert "low_activity" in risk_types

    def test_detects_milestone_deadline_risk(self, analyzer: ProjectAnalyzer) -> None:
        now = datetime.utcnow()
        urgent_project = {
            "tasks": [],
            "milestones": [
                {"id": str(uuid4()), "title": "Urgent M", "is_completed": False,
                 "target_date": (now + timedelta(days=3)).isoformat()},
            ],
        }
        risks = analyzer.detect_risks(urgent_project)
        risk_types = [r["type"] for r in risks]
        assert "milestone_deadline" in risk_types

    def test_risk_has_required_fields(self, analyzer: ProjectAnalyzer, critical_project: dict) -> None:
        risks = analyzer.detect_risks(critical_project)
        for risk in risks:
            assert "type" in risk
            assert "severity" in risk
            assert "description" in risk
            assert "impact" in risk
            assert "mitigation" in risk

    def test_overdue_tasks_risk_severity_is_high(self, analyzer: ProjectAnalyzer, critical_project: dict) -> None:
        risks = analyzer.detect_risks(critical_project)
        overdue_risk = next((r for r in risks if r["type"] == "overdue_tasks"), None)
        assert overdue_risk is not None
        assert overdue_risk["severity"] == "high"


class TestPredictCompletion:
    def test_empty_project_returns_low_confidence(self, analyzer: ProjectAnalyzer, empty_project: dict) -> None:
        result = analyzer.predict_completion(empty_project)
        assert result["confidence"] == "low"
        assert result["predicted_date"] is None

    def test_no_completed_tasks_low_confidence(self, analyzer: ProjectAnalyzer) -> None:
        project = {
            "tasks": [
                {"id": str(uuid4()), "status": "todo"},
                {"id": str(uuid4()), "status": "in_progress"},
            ]
        }
        result = analyzer.predict_completion(project)
        assert result["confidence"] == "low"
        assert result["predicted_date"] is None

    def test_high_completion_rate_high_confidence(self, analyzer: ProjectAnalyzer) -> None:
        tasks = [{"id": str(uuid4()), "status": "done"} for _ in range(8)]
        tasks.append({"id": str(uuid4()), "status": "in_progress"})
        tasks.append({"id": str(uuid4()), "status": "todo"})
        project = {"tasks": tasks}
        result = analyzer.predict_completion(project)
        assert result["confidence"] == "high"
        assert result["predicted_date"] is not None

    def test_prediction_contains_reasoning(self, analyzer: ProjectAnalyzer, healthy_project: dict) -> None:
        result = analyzer.predict_completion(healthy_project)
        assert "reasoning" in result
        assert len(result["reasoning"]) > 0

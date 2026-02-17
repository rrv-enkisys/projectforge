"""Factory functions for creating test data."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from src.clients.models import Client
from src.milestones.models import Milestone, MilestoneStatus
from src.organizations.models import Organization
from src.projects.models import Project, ProjectStatus
from src.tasks.models import Task, TaskPriority, TaskStatus
from src.users.models import OrgRole, User, UserOrganization


def create_organization(
    organization_id: UUID | None = None,
    name: str = "Test Organization",
    slug: str = "test-org",
    **kwargs: Any,
) -> Organization:
    """Create a test organization."""
    return Organization(
        id=organization_id or uuid4(),
        name=name,
        slug=slug,
        settings=kwargs.get("settings", {}),
        branding=kwargs.get("branding", {}),
    )


def create_user(
    user_id: UUID | None = None,
    firebase_uid: str = "test-firebase-uid",
    email: str = "test@example.com",
    **kwargs: Any,
) -> User:
    """Create a test user."""
    return User(
        id=user_id or uuid4(),
        firebase_uid=firebase_uid,
        email=email,
        display_name=kwargs.get("display_name", "Test User"),
        photo_url=kwargs.get("photo_url"),
        settings=kwargs.get("settings", {}),
    )


def create_user_organization(
    user_id: UUID,
    organization_id: UUID,
    role: OrgRole = OrgRole.MEMBER,
    **kwargs: Any,
) -> UserOrganization:
    """Create a test user-organization relationship."""
    return UserOrganization(
        user_id=user_id,
        organization_id=organization_id,
        role=role,
    )


def create_client(
    organization_id: UUID,
    client_id: UUID | None = None,
    name: str = "Test Client",
    **kwargs: Any,
) -> Client:
    """Create a test client."""
    return Client(
        id=client_id or uuid4(),
        organization_id=organization_id,
        name=name,
        email=kwargs.get("email"),
        phone=kwargs.get("phone"),
        company=kwargs.get("company"),
        address=kwargs.get("address"),
        notes=kwargs.get("notes"),
        settings=kwargs.get("settings", {}),
    )


def create_project(
    organization_id: UUID,
    project_id: UUID | None = None,
    name: str = "Test Project",
    client_id: UUID | None = None,
    status: ProjectStatus = ProjectStatus.PLANNING,
    **kwargs: Any,
) -> Project:
    """Create a test project."""
    today = date.today()
    return Project(
        id=project_id or uuid4(),
        organization_id=organization_id,
        name=name,
        description=kwargs.get("description", "Test project description"),
        client_id=client_id,
        status=status,
        start_date=kwargs.get("start_date", today),
        end_date=kwargs.get("end_date", today + timedelta(days=30)),
        budget=kwargs.get("budget", 10000.0),
        settings=kwargs.get("settings", {}),
    )


def create_milestone(
    organization_id: UUID,
    project_id: UUID,
    milestone_id: UUID | None = None,
    name: str = "Test Milestone",
    status: MilestoneStatus = MilestoneStatus.PLANNING,
    **kwargs: Any,
) -> Milestone:
    """Create a test milestone."""
    return Milestone(
        id=milestone_id or uuid4(),
        organization_id=organization_id,
        project_id=project_id,
        name=name,
        description=kwargs.get("description", "Test milestone description"),
        target_date=kwargs.get("target_date", date.today() + timedelta(days=15)),
        status=status,
    )


def create_task(
    organization_id: UUID,
    project_id: UUID,
    task_id: UUID | None = None,
    title: str = "Test Task",
    milestone_id: UUID | None = None,
    parent_task_id: UUID | None = None,
    status: TaskStatus = TaskStatus.TODO,
    priority: TaskPriority = TaskPriority.MEDIUM,
    **kwargs: Any,
) -> Task:
    """Create a test task."""
    return Task(
        id=task_id or uuid4(),
        organization_id=organization_id,
        project_id=project_id,
        milestone_id=milestone_id,
        parent_task_id=parent_task_id,
        title=title,
        description=kwargs.get("description", "Test task description"),
        status=status,
        priority=priority,
        start_date=kwargs.get("start_date"),
        due_date=kwargs.get("due_date"),
        estimated_hours=kwargs.get("estimated_hours"),
        actual_hours=kwargs.get("actual_hours"),
        position=kwargs.get("position", 0),
    )

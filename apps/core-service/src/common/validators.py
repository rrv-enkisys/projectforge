"""Business validation utilities for the core service."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Callable
from uuid import UUID

from .exceptions import BusinessRuleError, ValidationError


class DateValidator:
    """Validator for date-related business rules."""

    @staticmethod
    def validate_date_range(
        start_date: date | None,
        end_date: date | None,
        field_name: str = "date",
    ) -> None:
        """Validate that end_date is after start_date."""
        if start_date and end_date and end_date < start_date:
            raise ValidationError(
                f"End date must be after start date (start: {start_date}, end: {end_date})",
                field=field_name,
            )

    @staticmethod
    def validate_date_within_range(
        check_date: date,
        start_date: date | None,
        end_date: date | None,
        field_name: str = "date",
        context: str = "project",
    ) -> None:
        """Validate that a date falls within a range."""
        if start_date and check_date < start_date:
            raise ValidationError(
                f"{field_name} ({check_date}) must be on or after {context} start date ({start_date})",
                field=field_name,
            )
        if end_date and check_date > end_date:
            raise ValidationError(
                f"{field_name} ({check_date}) must be on or before {context} end date ({end_date})",
                field=field_name,
            )

    @staticmethod
    def validate_future_date(check_date: date, field_name: str = "date") -> None:
        """Validate that a date is in the future."""
        today = date.today()
        if check_date < today:
            raise ValidationError(
                f"{field_name} must be in the future (provided: {check_date}, today: {today})",
                field=field_name,
            )


class BudgetValidator:
    """Validator for budget-related business rules."""

    @staticmethod
    def validate_positive_amount(amount: float | Decimal | None, field_name: str = "amount") -> None:
        """Validate that an amount is positive."""
        if amount is not None and amount < 0:
            raise ValidationError(
                f"{field_name} must be positive (provided: {amount})",
                field=field_name,
            )

    @staticmethod
    def validate_budget_allocation(
        total_budget: float | Decimal | None,
        allocated_budget: float | Decimal,
        field_name: str = "budget",
    ) -> None:
        """Validate that allocated budget doesn't exceed total."""
        if total_budget is not None and allocated_budget > total_budget:
            raise BusinessRuleError(
                f"Allocated budget ({allocated_budget}) exceeds total budget ({total_budget})",
                rule="budget_allocation",
            )


class StatusValidator:
    """Validator for status transition rules."""

    # Valid status transitions for projects
    PROJECT_TRANSITIONS = {
        "planning": ["active", "on_hold", "cancelled"],
        "active": ["on_hold", "completed", "cancelled"],
        "on_hold": ["active", "cancelled"],
        "completed": [],  # Terminal state
        "cancelled": [],  # Terminal state
    }

    # Valid status transitions for tasks
    TASK_TRANSITIONS = {
        "todo": ["in_progress", "cancelled"],
        "in_progress": ["review", "blocked", "cancelled"],
        "review": ["done", "in_progress", "cancelled"],
        "blocked": ["todo", "in_progress", "cancelled"],
        "done": [],  # Terminal state
        "cancelled": [],  # Terminal state
    }

    # Valid status transitions for milestones
    MILESTONE_TRANSITIONS = {
        "planning": ["in_progress", "cancelled"],
        "in_progress": ["completed", "at_risk", "cancelled"],
        "at_risk": ["in_progress", "completed", "cancelled"],
        "completed": [],  # Terminal state
        "cancelled": [],  # Terminal state
    }

    @staticmethod
    def validate_status_transition(
        current_status: str,
        new_status: str,
        transitions: dict[str, list[str]],
        entity_type: str = "entity",
    ) -> None:
        """Validate that a status transition is allowed."""
        if current_status == new_status:
            return  # No change is always valid

        allowed_transitions = transitions.get(current_status, [])
        if new_status not in allowed_transitions:
            raise BusinessRuleError(
                f"Cannot transition {entity_type} from '{current_status}' to '{new_status}'. "
                f"Allowed transitions: {', '.join(allowed_transitions) if allowed_transitions else 'none (terminal state)'}",
                rule="status_transition",
            )


class DependencyValidator:
    """Validator for dependency-related business rules."""

    @staticmethod
    def detect_circular_dependency(
        item_id: UUID,
        parent_id: UUID | None,
        get_ancestors_fn: Callable[[UUID], list[UUID]],
    ) -> None:
        """Detect circular dependencies in hierarchical structures."""
        if parent_id is None:
            return

        if item_id == parent_id:
            raise BusinessRuleError(
                "An item cannot be its own parent",
                rule="circular_dependency",
            )

        # Get all ancestors of the proposed parent
        try:
            ancestors = get_ancestors_fn(parent_id)
        except BusinessRuleError:
            # Re-raise BusinessRuleError
            raise
        except Exception:
            # If we can't get ancestors for other reasons, allow it (parent might be new)
            return

        if item_id in ancestors:
            raise BusinessRuleError(
                "Circular dependency detected: parent is a descendant of this item",
                rule="circular_dependency",
            )


class OrganizationValidator:
    """Validator for multi-tenancy and organization isolation."""

    @staticmethod
    def validate_same_organization(
        org_id1: UUID,
        org_id2: UUID,
        entity1_type: str = "entity1",
        entity2_type: str = "entity2",
    ) -> None:
        """Validate that two entities belong to the same organization."""
        if org_id1 != org_id2:
            raise BusinessRuleError(
                f"{entity1_type} and {entity2_type} must belong to the same organization",
                rule="organization_isolation",
            )

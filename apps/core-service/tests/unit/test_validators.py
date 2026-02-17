"""Unit tests for business validators."""

from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from src.common.exceptions import BusinessRuleError, ValidationError
from src.common.validators import (
    BudgetValidator,
    DateValidator,
    DependencyValidator,
    OrganizationValidator,
    StatusValidator,
)


class TestDateValidator:
    """Tests for DateValidator."""

    def test_validate_date_range_valid(self) -> None:
        """Test valid date range."""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        # Should not raise
        DateValidator.validate_date_range(start_date, end_date)

    def test_validate_date_range_invalid(self) -> None:
        """Test invalid date range (end before start)."""
        start_date = date(2024, 12, 31)
        end_date = date(2024, 1, 1)
        with pytest.raises(ValidationError) as exc_info:
            DateValidator.validate_date_range(start_date, end_date)
        assert "End date must be after start date" in str(exc_info.value)

    def test_validate_date_range_none_values(self) -> None:
        """Test date range with None values."""
        # Should not raise
        DateValidator.validate_date_range(None, None)
        DateValidator.validate_date_range(date.today(), None)
        DateValidator.validate_date_range(None, date.today())

    def test_validate_date_within_range_valid(self) -> None:
        """Test date within valid range."""
        check_date = date(2024, 6, 15)
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        # Should not raise
        DateValidator.validate_date_within_range(check_date, start_date, end_date)

    def test_validate_date_within_range_before_start(self) -> None:
        """Test date before range start."""
        check_date = date(2023, 12, 15)
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        with pytest.raises(ValidationError) as exc_info:
            DateValidator.validate_date_within_range(check_date, start_date, end_date)
        assert "must be on or after" in str(exc_info.value)

    def test_validate_date_within_range_after_end(self) -> None:
        """Test date after range end."""
        check_date = date(2025, 1, 15)
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        with pytest.raises(ValidationError) as exc_info:
            DateValidator.validate_date_within_range(check_date, start_date, end_date)
        assert "must be on or before" in str(exc_info.value)


class TestBudgetValidator:
    """Tests for BudgetValidator."""

    def test_validate_positive_amount_valid(self) -> None:
        """Test positive amount validation with valid value."""
        # Should not raise
        BudgetValidator.validate_positive_amount(100.0)
        BudgetValidator.validate_positive_amount(Decimal("100.50"))

    def test_validate_positive_amount_zero(self) -> None:
        """Test zero amount (valid)."""
        # Should not raise - zero is valid
        BudgetValidator.validate_positive_amount(0.0)

    def test_validate_positive_amount_negative(self) -> None:
        """Test negative amount (invalid)."""
        with pytest.raises(ValidationError) as exc_info:
            BudgetValidator.validate_positive_amount(-100.0)
        assert "must be positive" in str(exc_info.value)

    def test_validate_positive_amount_none(self) -> None:
        """Test None amount (valid)."""
        # Should not raise
        BudgetValidator.validate_positive_amount(None)

    def test_validate_budget_allocation_valid(self) -> None:
        """Test valid budget allocation."""
        # Should not raise
        BudgetValidator.validate_budget_allocation(1000.0, 500.0)

    def test_validate_budget_allocation_exceeds(self) -> None:
        """Test budget allocation exceeds total."""
        with pytest.raises(BusinessRuleError) as exc_info:
            BudgetValidator.validate_budget_allocation(1000.0, 1500.0)
        assert "exceeds total budget" in str(exc_info.value)

    def test_validate_budget_allocation_no_total(self) -> None:
        """Test budget allocation with no total budget."""
        # Should not raise - no limit if total is None
        BudgetValidator.validate_budget_allocation(None, 1500.0)


class TestStatusValidator:
    """Tests for StatusValidator."""

    def test_validate_project_status_transition_valid(self) -> None:
        """Test valid project status transition."""
        # Should not raise
        StatusValidator.validate_status_transition(
            "planning", "active", StatusValidator.PROJECT_TRANSITIONS, "project"
        )

    def test_validate_project_status_transition_invalid(self) -> None:
        """Test invalid project status transition."""
        with pytest.raises(BusinessRuleError) as exc_info:
            StatusValidator.validate_status_transition(
                "completed", "active", StatusValidator.PROJECT_TRANSITIONS, "project"
            )
        assert "Cannot transition" in str(exc_info.value)
        assert "completed" in str(exc_info.value)
        assert "active" in str(exc_info.value)

    def test_validate_task_status_transition_valid(self) -> None:
        """Test valid task status transition."""
        # Should not raise
        StatusValidator.validate_status_transition(
            "todo", "in_progress", StatusValidator.TASK_TRANSITIONS, "task"
        )

    def test_validate_task_status_transition_invalid(self) -> None:
        """Test invalid task status transition."""
        with pytest.raises(BusinessRuleError) as exc_info:
            StatusValidator.validate_status_transition(
                "todo", "done", StatusValidator.TASK_TRANSITIONS, "task"
            )
        assert "Cannot transition" in str(exc_info.value)

    def test_validate_status_transition_no_change(self) -> None:
        """Test status transition with no change."""
        # Should not raise - same status is always valid
        StatusValidator.validate_status_transition(
            "active", "active", StatusValidator.PROJECT_TRANSITIONS, "project"
        )


class TestDependencyValidator:
    """Tests for DependencyValidator."""

    def test_detect_circular_dependency_self_parent(self) -> None:
        """Test circular dependency - item as its own parent."""
        item_id = uuid4()
        with pytest.raises(BusinessRuleError) as exc_info:
            DependencyValidator.detect_circular_dependency(
                item_id, item_id, lambda x: []
            )
        assert "cannot be its own parent" in str(exc_info.value)

    def test_detect_circular_dependency_in_ancestors(self) -> None:
        """Test circular dependency - parent is descendant."""
        item_id = uuid4()
        parent_id = uuid4()

        def get_ancestors(pid):  # type: ignore
            # Simulate that parent has item_id as ancestor
            return [item_id]

        with pytest.raises(BusinessRuleError) as exc_info:
            DependencyValidator.detect_circular_dependency(
                item_id, parent_id, get_ancestors
            )
        assert "Circular dependency detected" in str(exc_info.value)

    def test_detect_circular_dependency_valid(self) -> None:
        """Test valid dependency (no circular)."""
        item_id = uuid4()
        parent_id = uuid4()

        def get_ancestors(pid):  # type: ignore
            # Parent has no ancestors
            return []

        # Should not raise
        DependencyValidator.detect_circular_dependency(
            item_id, parent_id, get_ancestors
        )

    def test_detect_circular_dependency_none_parent(self) -> None:
        """Test with None parent."""
        item_id = uuid4()
        # Should not raise
        DependencyValidator.detect_circular_dependency(item_id, None, lambda x: [])


class TestOrganizationValidator:
    """Tests for OrganizationValidator."""

    def test_validate_same_organization_valid(self) -> None:
        """Test same organization validation with matching IDs."""
        org_id = uuid4()
        # Should not raise
        OrganizationValidator.validate_same_organization(org_id, org_id)

    def test_validate_same_organization_invalid(self) -> None:
        """Test same organization validation with different IDs."""
        org_id1 = uuid4()
        org_id2 = uuid4()
        with pytest.raises(BusinessRuleError) as exc_info:
            OrganizationValidator.validate_same_organization(
                org_id1, org_id2, "Project", "Task"
            )
        assert "must belong to the same organization" in str(exc_info.value)

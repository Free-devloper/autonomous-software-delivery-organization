import uuid
from datetime import UTC, datetime
from uuid import UUID

from autonomous_sdo_api.planning.dag import validate_and_sort_dag
from autonomous_sdo_api.planning.models import (
    ArchitecturePlan,
    BudgetExceededError,
    DagEdge,
    PlanNotFoundError,
    WorkPackage,
    WorkPackageBudget,
)


class ArchitecturePlanningService:
    """Decomposes requirements into bounded work packages with DAG validation and budget safety."""

    def __init__(self) -> None:
        # Storage keyed by (org_id, plan_id) -> ArchitecturePlan
        self._plans: dict[tuple[UUID, str], ArchitecturePlan] = {}

    def create_plan(
        self,
        org_id: UUID,
        requirement_id: str,
        revision_id: str,
        summary: str,
        work_packages: list[WorkPackage],
        edges: list[DagEdge] | None = None,
        max_allowed_budget: WorkPackageBudget | None = None,
    ) -> ArchitecturePlan:
        """Validate DAG topology, compute aggregate budget, and persist architecture plan."""
        actual_edges = edges or []

        # Validate DAG & cycle detection
        validate_and_sort_dag(work_packages, actual_edges)

        # Compute aggregate budget
        total_tokens = sum(wp.budget.max_tokens for wp in work_packages)
        total_duration = sum(wp.budget.max_duration_seconds for wp in work_packages)
        total_cost = round(sum(wp.budget.max_cost_usd for wp in work_packages), 2)

        total_budget = WorkPackageBudget(
            max_tokens=total_tokens,
            max_duration_seconds=total_duration,
            max_cost_usd=total_cost,
        )

        if max_allowed_budget is not None:
            if total_tokens > max_allowed_budget.max_tokens:
                msg = (
                    f"Token budget {total_tokens} exceeds allowed {max_allowed_budget.max_tokens}."
                )
                raise BudgetExceededError(msg)
            if total_cost > max_allowed_budget.max_cost_usd:
                msg = f"Cost ${total_cost} exceeds allowed ${max_allowed_budget.max_cost_usd}."
                raise BudgetExceededError(msg)

        plan_id = f"plan_{uuid.uuid4().hex[:12]}"
        now = datetime.now(UTC)

        plan = ArchitecturePlan(
            id=plan_id,
            requirement_id=requirement_id,
            revision_id=revision_id,
            summary=summary,
            work_packages=work_packages,
            edges=actual_edges,
            total_budget=total_budget,
            is_approved=False,
            created_at=now,
        )

        self._plans[(org_id, plan_id)] = plan
        return plan

    def get_plan(self, org_id: UUID, plan_id: str) -> ArchitecturePlan:
        """Fetch an architecture plan by ID within the tenant organization."""
        plan = self._plans.get((org_id, plan_id))
        if not plan:
            raise PlanNotFoundError(f"Plan '{plan_id}' not found in organization.")
        return plan

    def list_plans_for_requirement(
        self, org_id: UUID, requirement_id: str
    ) -> list[ArchitecturePlan]:
        """Fetch all plans created for a specific requirement."""
        return [
            p
            for (stored_org, _), p in self._plans.items()
            if stored_org == org_id and p.requirement_id == requirement_id
        ]

    def approve_plan(
        self,
        org_id: UUID,
        plan_id: str,
        rationale: str,
        approver_id: str,
    ) -> ArchitecturePlan:
        """Approve an architecture plan for subsequent workflow execution."""
        plan = self.get_plan(org_id, plan_id)
        now = datetime.now(UTC)

        approved_plan = ArchitecturePlan(
            id=plan.id,
            requirement_id=plan.requirement_id,
            revision_id=plan.revision_id,
            summary=plan.summary,
            work_packages=plan.work_packages,
            edges=plan.edges,
            total_budget=plan.total_budget,
            is_approved=True,
            approval_rationale=rationale,
            approved_by=approver_id,
            approved_at=now,
            created_at=plan.created_at,
        )

        self._plans[(org_id, plan_id)] = approved_plan
        return approved_plan

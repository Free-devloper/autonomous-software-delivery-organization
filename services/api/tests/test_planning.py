from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from autonomous_sdo_api.app import create_app
from autonomous_sdo_api.config import Settings
from autonomous_sdo_api.database.tenancy import OrganizationContext, get_organization_context
from autonomous_sdo_api.planning import (
    ArchitecturePlanningService,
    BudgetExceededError,
    CyclicDependencyError,
    DagEdge,
    PlanningError,
    PlanNotFoundError,
    SpecialistRole,
    WorkPackage,
    WorkPackageBudget,
    WorkPackageStatus,
    validate_and_sort_dag,
)
from autonomous_sdo_api.policy import Role

pytestmark = pytest.mark.unit


def _create_sample_wp(wp_id: str, deps: list[str] | None = None) -> WorkPackage:
    return WorkPackage(
        id=wp_id,
        requirement_id="req-1",
        revision_id="rev-1",
        title=f"Work package {wp_id}",
        description=f"Description for {wp_id}",
        target_files=[f"src/{wp_id}.py"],
        acceptance_criteria_ids=["ac-1"],
        dependencies=deps or [],
        assigned_specialist=SpecialistRole.BACKEND,
        budget=WorkPackageBudget(max_tokens=10000, max_duration_seconds=60, max_cost_usd=0.5),
        status=WorkPackageStatus.PENDING,
        created_at=datetime.now(UTC),
    )


# ---------------------------------------------------------------------------
# DAG Validation Tests
# ---------------------------------------------------------------------------


def test_dag_validation_and_topological_sort() -> None:
    wp_a = _create_sample_wp("wp_a")
    wp_b = _create_sample_wp("wp_b")
    wp_c = _create_sample_wp("wp_c")

    # A -> B -> C
    edges = [
        DagEdge(from_package_id="wp_a", to_package_id="wp_b"),
        DagEdge(from_package_id="wp_b", to_package_id="wp_c"),
    ]

    order = validate_and_sort_dag([wp_a, wp_b, wp_c], edges)
    assert order == ["wp_a", "wp_b", "wp_c"]


def test_dag_cycle_detection() -> None:
    wp_a = _create_sample_wp("wp_a")
    wp_b = _create_sample_wp("wp_b")

    # Circular: A -> B, B -> A
    edges = [
        DagEdge(from_package_id="wp_a", to_package_id="wp_b"),
        DagEdge(from_package_id="wp_b", to_package_id="wp_a"),
    ]

    with pytest.raises(CyclicDependencyError):
        validate_and_sort_dag([wp_a, wp_b], edges)

    # Self-reference
    self_edge = [DagEdge(from_package_id="wp_a", to_package_id="wp_a")]
    with pytest.raises(CyclicDependencyError):
        validate_and_sort_dag([wp_a], self_edge)


def test_dag_missing_node_errors() -> None:
    wp_a = _create_sample_wp("wp_a")
    edge = DagEdge(from_package_id="wp_a", to_package_id="missing_node")

    with pytest.raises(PlanningError):
        validate_and_sort_dag([wp_a], [edge])


# ---------------------------------------------------------------------------
# Planning Service & Budget Safety Tests
# ---------------------------------------------------------------------------


def test_planning_service_and_budget() -> None:
    service = ArchitecturePlanningService()
    org_id = uuid4()

    wp1 = _create_sample_wp("wp1")
    wp2 = _create_sample_wp("wp2")

    plan = service.create_plan(
        org_id=org_id,
        requirement_id="req-1",
        revision_id="rev-1",
        summary="Plan for Req 1",
        work_packages=[wp1, wp2],
        edges=[DagEdge(from_package_id="wp1", to_package_id="wp2")],
    )

    assert plan.total_budget.max_tokens == 20000
    assert plan.total_budget.max_duration_seconds == 120
    assert plan.total_budget.max_cost_usd == 1.0
    assert plan.is_approved is False

    # Approve plan
    approved = service.approve_plan(
        org_id=org_id,
        plan_id=plan.id,
        rationale="Approved by lead architect",
        approver_id="usr-lead-1",
    )
    assert approved.is_approved is True
    assert approved.approval_rationale == "Approved by lead architect"
    assert approved.approved_by == "usr-lead-1"
    assert approved.approved_at is not None

    # Budget limit exceeded
    limit_budget = WorkPackageBudget(max_tokens=5000, max_cost_usd=0.2)
    with pytest.raises(BudgetExceededError):
        service.create_plan(
            org_id=org_id,
            requirement_id="req-1",
            revision_id="rev-1",
            summary="Overbudget Plan",
            work_packages=[wp1, wp2],
            max_allowed_budget=limit_budget,
        )


def test_planning_tenant_isolation() -> None:
    service = ArchitecturePlanningService()
    org_a = uuid4()
    org_b = uuid4()

    wp1 = _create_sample_wp("wp1")
    plan_a = service.create_plan(
        org_id=org_a,
        requirement_id="req-1",
        revision_id="rev-1",
        summary="Tenant A Plan",
        work_packages=[wp1],
    )

    assert service.get_plan(org_a, plan_a.id).id == plan_a.id

    with pytest.raises(PlanNotFoundError):
        service.get_plan(org_b, plan_a.id)

    assert len(service.list_plans_for_requirement(org_b, "req-1")) == 0


# ---------------------------------------------------------------------------
# Planning API Route Tests
# ---------------------------------------------------------------------------


def test_planning_api_routes() -> None:
    settings = Settings(service_name="asdo-plan-test")
    app = create_app(settings=settings)
    client = TestClient(app)
    org_id = UUID("018f0000-0000-7000-8000-000000000001")

    app.dependency_overrides[get_organization_context] = lambda: OrganizationContext(
        organization_id=org_id,
        actor_id="usr-plan-1",
        roles=frozenset({Role.REPOSITORY_MAINTAINER}),
    )

    # 1. Create plan
    res_create = client.post(
        "/api/v1/planning/plans",
        json={
            "requirement_id": "req-101",
            "revision_id": "rev-101",
            "summary": "Full authentication pipeline decomposition",
            "work_packages": [
                {
                    "id": "wp_be",
                    "requirement_id": "req-101",
                    "revision_id": "rev-101",
                    "title": "Backend Routes",
                    "description": "API handlers",
                    "target_files": ["services/api/routes.py"],
                    "acceptance_criteria_ids": ["ac-1"],
                    "dependencies": [],
                    "assigned_specialist": "backend",
                    "budget": {
                        "max_tokens": 15000,
                        "max_duration_seconds": 120,
                        "max_cost_usd": 0.5,
                    },
                    "status": "pending",
                    "created_at": "2026-08-20T00:00:00Z",
                },
                {
                    "id": "wp_fe",
                    "requirement_id": "req-101",
                    "revision_id": "rev-101",
                    "title": "Frontend UI",
                    "description": "Next.js UI",
                    "target_files": ["apps/web/page.tsx"],
                    "acceptance_criteria_ids": ["ac-1"],
                    "dependencies": ["wp_be"],
                    "assigned_specialist": "frontend",
                    "budget": {
                        "max_tokens": 15000,
                        "max_duration_seconds": 120,
                        "max_cost_usd": 0.5,
                    },
                    "status": "pending",
                    "created_at": "2026-08-20T00:00:00Z",
                },
            ],
            "edges": [{"from_package_id": "wp_be", "to_package_id": "wp_fe"}],
        },
    )
    assert res_create.status_code == 201
    plan_data = res_create.json()
    plan_id = plan_data["id"]
    assert plan_data["total_budget"]["max_tokens"] == 30000

    # 2. Get plan
    res_get = client.get(f"/api/v1/planning/plans/{plan_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == plan_id

    # 3. List plans
    res_list = client.get("/api/v1/planning/plans?requirement_id=req-101")
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    # 4. Approve plan
    res_approve = client.post(
        f"/api/v1/planning/plans/{plan_id}/approve",
        json={"rationale": "Plan decomposition conforms to ADR-0003 standards."},
    )
    assert res_approve.status_code == 200
    assert res_approve.json()["is_approved"] is True
    assert (
        res_approve.json()["approval_rationale"]
        == "Plan decomposition conforms to ADR-0003 standards."
    )

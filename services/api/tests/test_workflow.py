from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from autonomous_sdo_api.app import create_app
from autonomous_sdo_api.config import Settings
from autonomous_sdo_api.database.tenancy import OrganizationContext, get_organization_context
from autonomous_sdo_api.policy import Role
from autonomous_sdo_api.workflow import (
    InvalidWorkflowStateTransitionError,
    WorkflowExecutionEngine,
    WorkflowNode,
    WorkflowNotFoundError,
    WorkflowState,
)

pytestmark = pytest.mark.unit


def test_workflow_start_and_approval_pause() -> None:
    engine = WorkflowExecutionEngine()
    org_id = uuid4()

    wf = engine.start_workflow(
        org_id=org_id,
        requirement_id="req-auth",
        plan_id="plan-1",
        initial_payload={"branch": "main"},
        actor_id="usr-1",
    )

    assert wf.state == WorkflowState.AWAITING_APPROVAL
    assert wf.current_node == WorkflowNode.AWAITING_HUMAN_APPROVAL
    assert wf.step_count == 3

    checkpoints = engine.list_checkpoints(org_id, wf.id)
    assert len(checkpoints) == 3
    assert checkpoints[0].node_name == WorkflowNode.REQUIREMENTS_ANALYSIS
    assert checkpoints[1].node_name == WorkflowNode.PLANNING_AND_BUDGET
    assert checkpoints[2].node_name == WorkflowNode.AWAITING_HUMAN_APPROVAL


def test_workflow_approval_progression() -> None:
    engine = WorkflowExecutionEngine()
    org_id = uuid4()

    wf = engine.start_workflow(
        org_id=org_id,
        requirement_id="req-auth",
        actor_id="usr-1",
    )

    # Approve
    completed_wf = engine.send_signal(
        org_id=org_id,
        workflow_id=wf.id,
        signal_name="approve",
        payload={"rationale": "Approved by architect"},
        actor_id="usr-lead",
    )

    assert completed_wf.state == WorkflowState.COMPLETED
    assert completed_wf.current_node == WorkflowNode.REVIEW_AND_SIGNOFF
    assert completed_wf.step_count == 6

    checkpoints = engine.list_checkpoints(org_id, wf.id)
    assert len(checkpoints) == 6
    assert checkpoints[3].node_name == WorkflowNode.EXECUTION_DISPATCH
    assert checkpoints[4].node_name == WorkflowNode.VERIFICATION_AND_TESTING
    assert checkpoints[5].node_name == WorkflowNode.REVIEW_AND_SIGNOFF


def test_workflow_interrupt_and_resume() -> None:
    engine = WorkflowExecutionEngine()
    org_id = uuid4()

    wf = engine.start_workflow(
        org_id=org_id,
        requirement_id="req-auth",
        actor_id="usr-1",
    )

    # Interrupt
    paused = engine.send_signal(org_id, wf.id, "interrupt")
    assert paused.state == WorkflowState.PAUSED

    # Resume
    resumed = engine.send_signal(org_id, wf.id, "resume")
    assert resumed.state == WorkflowState.AWAITING_APPROVAL

    # Reject
    cancelled = engine.send_signal(org_id, wf.id, "reject")
    assert cancelled.state == WorkflowState.CANCELLED

    # Invalid resume on non-paused
    with pytest.raises(InvalidWorkflowStateTransitionError):
        engine.send_signal(org_id, wf.id, "resume")


def test_workflow_rollback_checkpoint() -> None:
    engine = WorkflowExecutionEngine()
    org_id = uuid4()

    wf = engine.start_workflow(
        org_id=org_id,
        requirement_id="req-auth",
        actor_id="usr-1",
    )

    checkpoints = engine.list_checkpoints(org_id, wf.id)
    step1_chk = checkpoints[1]  # PLANNING_AND_BUDGET

    rolled_back = engine.rollback_to_checkpoint(org_id, wf.id, step1_chk.id)
    assert rolled_back.current_node == WorkflowNode.PLANNING_AND_BUDGET
    assert rolled_back.step_count == 2
    assert rolled_back.state == WorkflowState.RUNNING


def test_workflow_tenant_isolation() -> None:
    engine = WorkflowExecutionEngine()
    org_a = uuid4()
    org_b = uuid4()

    wf_a = engine.start_workflow(org_id=org_a, requirement_id="req-a")

    assert engine.get_workflow(org_a, wf_a.id).id == wf_a.id

    with pytest.raises(WorkflowNotFoundError):
        engine.get_workflow(org_b, wf_a.id)

    with pytest.raises(WorkflowNotFoundError):
        engine.list_checkpoints(org_b, wf_a.id)


def test_workflow_api_routes() -> None:
    settings = Settings(service_name="asdo-wf-test")
    app = create_app(settings=settings)
    client = TestClient(app)
    org_id = UUID("018f0000-0000-7000-8000-000000000001")

    app.dependency_overrides[get_organization_context] = lambda: OrganizationContext(
        organization_id=org_id,
        actor_id="usr-wf-1",
        roles=frozenset({Role.REPOSITORY_MAINTAINER}),
    )

    # 1. Start workflow
    res_start = client.post(
        "/api/v1/workflows",
        json={
            "requirement_id": "req-101",
            "plan_id": "plan-101",
            "initial_payload": {"repo": "asdo"},
        },
    )
    assert res_start.status_code == 201
    wf_data = res_start.json()
    wf_id = wf_data["id"]
    assert wf_data["state"] == "awaiting_approval"

    # 2. Get workflow
    res_get = client.get(f"/api/v1/workflows/{wf_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == wf_id

    # 3. List checkpoints
    res_chk = client.get(f"/api/v1/workflows/{wf_id}/checkpoints")
    assert res_chk.status_code == 200
    checkpoints = res_chk.json()
    assert len(checkpoints) == 3

    # 4. Signal approve
    res_sig = client.post(
        f"/api/v1/workflows/{wf_id}/signal",
        json={"signal_name": "approve", "payload": {"rationale": "Approved for dispatch"}},
    )
    assert res_sig.status_code == 200
    assert res_sig.json()["state"] == "completed"

    # 5. Rollback to step 0
    res_roll = client.post(
        f"/api/v1/workflows/{wf_id}/rollback",
        json={"checkpoint_id": checkpoints[0]["id"]},
    )
    assert res_roll.status_code == 200
    assert res_roll.json()["current_node"] == "requirements_analysis"

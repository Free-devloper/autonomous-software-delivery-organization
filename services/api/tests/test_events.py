import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from autonomous_sdo_api.app import create_app
from autonomous_sdo_api.config import Settings
from autonomous_sdo_api.database.tenancy import OrganizationContext, get_organization_context
from autonomous_sdo_api.events import WorkflowEvent, WorkflowEventBroker, WorkflowEventType
from autonomous_sdo_api.policy import Role
from autonomous_sdo_api.workflow.models import WorkflowNode

pytestmark = pytest.mark.unit


@pytest.mark.anyio
async def test_event_broker_publish_and_history() -> None:
    broker = WorkflowEventBroker()
    org_id = uuid4()
    wf_id = "wf-test-1"
    now = datetime.now(UTC)

    evt1 = WorkflowEvent(
        id="evt-1",
        workflow_id=wf_id,
        event_type=WorkflowEventType.NODE_TRANSITION,
        node_name=WorkflowNode.REQUIREMENTS_ANALYSIS,
        payload={"info": "started"},
        timestamp=now,
    )
    evt2 = WorkflowEvent(
        id="evt-2",
        workflow_id=wf_id,
        event_type=WorkflowEventType.TOKEN_USAGE,
        node_name=WorkflowNode.PLANNING_AND_BUDGET,
        payload={"tokens_used": 500},
        timestamp=now,
    )

    broker.publish(org_id, evt1)
    broker.publish(org_id, evt2)

    history = broker.get_history(org_id, wf_id)
    assert len(history) == 2
    assert history[0].id == "evt-1"
    assert history[1].id == "evt-2"


@pytest.mark.anyio
async def test_event_broker_subscription() -> None:
    broker = WorkflowEventBroker()
    org_id = uuid4()
    wf_id = "wf-test-sub"
    now = datetime.now(UTC)

    evt = WorkflowEvent(
        id="evt-past",
        workflow_id=wf_id,
        event_type=WorkflowEventType.NODE_TRANSITION,
        node_name=WorkflowNode.REQUIREMENTS_ANALYSIS,
        payload={},
        timestamp=now,
    )
    broker.publish(org_id, evt)

    # Subscribe and verify past event is replayed immediately
    received = []

    async def _consume() -> None:
        async for e in broker.subscribe(org_id, wf_id, replay_history=True):
            received.append(e)
            if len(received) == 2:
                break

    task = asyncio.create_task(_consume())
    await asyncio.sleep(0.01)

    # Publish new event
    evt_new = WorkflowEvent(
        id="evt-new",
        workflow_id=wf_id,
        event_type=WorkflowEventType.TOKEN_USAGE,
        node_name=WorkflowNode.PLANNING_AND_BUDGET,
        payload={"tokens": 100},
        timestamp=now,
    )
    broker.publish(org_id, evt_new)

    await task
    assert len(received) == 2
    assert received[0].id == "evt-past"
    assert received[1].id == "evt-new"


@pytest.mark.anyio
async def test_event_stream_generator() -> None:
    from autonomous_sdo_api.events.routes import _event_stream_generator

    broker = WorkflowEventBroker()
    org_id = UUID("018f0000-0000-7000-8000-000000000001")
    wf_id = "wf-sse-test"
    context = OrganizationContext(
        organization_id=org_id,
        actor_id="usr-sse-1",
        roles=frozenset({Role.REPOSITORY_MAINTAINER}),
    )

    evt = WorkflowEvent(
        id="evt-sse-1",
        workflow_id=wf_id,
        event_type=WorkflowEventType.NODE_TRANSITION,
        node_name=WorkflowNode.REQUIREMENTS_ANALYSIS,
        payload={"step": 0},
        timestamp=datetime.now(UTC),
    )
    broker.publish(org_id, evt)

    events = []
    async for sse_chunk in _event_stream_generator(broker, context, wf_id):
        events.append(sse_chunk)
        if len(events) >= 1:
            break

    assert len(events) == 1
    assert "id: evt-sse-1" in events[0]
    assert "event: node_transition" in events[0]
    assert "data: {" in events[0]


@pytest.mark.anyio
async def test_event_broker_last_event_id_offset() -> None:
    broker = WorkflowEventBroker()
    org_id = uuid4()
    wf_id = "wf-offset-test"
    now = datetime.now(UTC)

    e1 = WorkflowEvent(
        id="evt-1",
        workflow_id=wf_id,
        event_type=WorkflowEventType.NODE_TRANSITION,
        node_name=WorkflowNode.REQUIREMENTS_ANALYSIS,
        payload={},
        timestamp=now,
    )
    e2 = WorkflowEvent(
        id="evt-2",
        workflow_id=wf_id,
        event_type=WorkflowEventType.TOKEN_USAGE,
        node_name=WorkflowNode.PLANNING_AND_BUDGET,
        payload={},
        timestamp=now,
    )
    broker.publish(org_id, e1)
    broker.publish(org_id, e2)

    received = []
    async for item in broker.subscribe(org_id, wf_id, replay_history=True, last_event_id="evt-1"):
        received.append(item)
        if len(received) >= 1:
            break

    assert len(received) == 1
    assert received[0].id == "evt-2"


def test_workflow_sse_route_not_found() -> None:
    settings = Settings(service_name="asdo-sse-test")
    app = create_app(settings=settings)
    client = TestClient(app)
    org_id = UUID("018f0000-0000-7000-8000-000000000001")

    app.dependency_overrides[get_organization_context] = lambda: OrganizationContext(
        organization_id=org_id,
        actor_id="usr-sse-1",
        roles=frozenset({Role.REPOSITORY_MAINTAINER}),
    )

    response = client.get("/api/v1/workflows/nonexistent-id/events")
    assert response.status_code == 404
    assert "nonexistent-id" in response.json()["detail"]

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from autonomous_sdo_api.database.tenancy import OrganizationContext, get_organization_context
from autonomous_sdo_api.events.broker import WorkflowEventBroker
from autonomous_sdo_api.policy import Action, AuthorizationPolicy
from autonomous_sdo_api.workflow.engine import WorkflowExecutionEngine
from autonomous_sdo_api.workflow.models import WorkflowNotFoundError
from autonomous_sdo_api.workflow.routes import get_workflow_engine

router = APIRouter(prefix="/api/v1/workflows/{workflow_id}/events", tags=["Events"])

_AUTH_POLICY = AuthorizationPolicy()


async def _event_stream_generator(
    broker: WorkflowEventBroker,
    org_id: OrganizationContext,
    workflow_id: str,
    last_event_id: str | None = None,
) -> AsyncIterator[str]:
    async for event in broker.subscribe(
        org_id.organization_id, workflow_id, replay_history=True, last_event_id=last_event_id
    ):
        yield f"id: {event.id}\nevent: {event.event_type}\ndata: {event.model_dump_json()}\n\n"


@router.get(
    "",
    summary="Subscribe to live workflow Server-Sent Events stream",
    response_class=StreamingResponse,
)
async def subscribe_workflow_events(
    workflow_id: str,
    context: Annotated[OrganizationContext, Depends(get_organization_context)],
    engine: Annotated[WorkflowExecutionEngine, Depends(get_workflow_engine)],
    last_event_id_query: Annotated[str | None, Query(alias="last_event_id")] = None,
    last_event_id_header: Annotated[str | None, Header(alias="Last-Event-ID")] = None,
) -> StreamingResponse:
    _AUTH_POLICY.require(context.roles, Action.READ_WORKFLOWS)
    try:
        engine.get_workflow(context.organization_id, workflow_id)
    except WorkflowNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err

    effective_last_event_id = last_event_id_header or last_event_id_query

    return StreamingResponse(
        _event_stream_generator(
            engine.event_broker,
            context,
            workflow_id,
            last_event_id=effective_last_event_id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

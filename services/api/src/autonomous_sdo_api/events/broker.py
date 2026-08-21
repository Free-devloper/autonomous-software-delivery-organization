import asyncio
from collections.abc import AsyncIterator
from uuid import UUID

from autonomous_sdo_api.events.models import WorkflowEvent


class WorkflowEventBroker:
    """Multi-tenant in-memory pubsub broker for live workflow Server-Sent Events."""

    def __init__(self) -> None:
        # Storage keyed by (org_id, workflow_id) -> list[Queue]
        self._subscribers: dict[tuple[UUID, str], list[asyncio.Queue[WorkflowEvent]]] = {}
        # History buffer keyed by (org_id, workflow_id) -> list[WorkflowEvent]
        self._history: dict[tuple[UUID, str], list[WorkflowEvent]] = {}

    def publish(self, org_id: UUID, event: WorkflowEvent) -> None:
        """Broadcast an event to all active subscriber queues for the workflow."""
        key = (org_id, event.workflow_id)
        self._history.setdefault(key, []).append(event)

        queues = self._subscribers.get(key, [])
        for q in queues:
            q.put_nowait(event)

    def get_history(self, org_id: UUID, workflow_id: str) -> list[WorkflowEvent]:
        """Fetch historical events emitted for a workflow."""
        key = (org_id, workflow_id)
        return list(self._history.get(key, []))

    async def subscribe(
        self,
        org_id: UUID,
        workflow_id: str,
        replay_history: bool = True,
        last_event_id: str | None = None,
    ) -> AsyncIterator[WorkflowEvent]:
        """Subscribe to live workflow events with optional historical replay."""
        key = (org_id, workflow_id)
        queue: asyncio.Queue[WorkflowEvent] = asyncio.Queue()

        if key not in self._subscribers:
            self._subscribers[key] = []
        self._subscribers[key].append(queue)

        try:
            if replay_history:
                history = self._history.get(key, [])
                start_index = 0
                if last_event_id is not None:
                    for i, evt in enumerate(history):
                        if evt.id == last_event_id:
                            start_index = i + 1
                            break
                for past_event in history[start_index:]:
                    yield past_event

            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=0.2)
                    yield event
                except TimeoutError:
                    continue
                except asyncio.CancelledError:
                    break
        finally:
            if key in self._subscribers and queue in self._subscribers[key]:
                self._subscribers[key].remove(queue)
                if not self._subscribers[key]:
                    del self._subscribers[key]

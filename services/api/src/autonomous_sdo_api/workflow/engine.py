import uuid
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from autonomous_sdo_api.events.broker import WorkflowEventBroker
from autonomous_sdo_api.events.models import WorkflowEvent, WorkflowEventType
from autonomous_sdo_api.workflow.checkpoints import CheckpointStore
from autonomous_sdo_api.workflow.models import (
    InvalidWorkflowStateTransitionError,
    WorkflowCheckpoint,
    WorkflowExecution,
    WorkflowNode,
    WorkflowNotFoundError,
    WorkflowState,
)


class WorkflowExecutionEngine:
    """Durable workflow engine with zero-cost human approval wait states."""

    def __init__(
        self,
        checkpoint_store: CheckpointStore | None = None,
        event_broker: WorkflowEventBroker | None = None,
    ) -> None:
        self._checkpoints = checkpoint_store or CheckpointStore()
        self._broker = event_broker or WorkflowEventBroker()
        # Storage keyed by (org_id, workflow_id) -> WorkflowExecution
        self._executions: dict[tuple[UUID, str], WorkflowExecution] = {}

    @property
    def event_broker(self) -> WorkflowEventBroker:
        return self._broker

    def start_workflow(
        self,
        org_id: UUID,
        requirement_id: str,
        plan_id: str | None = None,
        initial_payload: dict[str, Any] | None = None,
        actor_id: str = "system",
    ) -> WorkflowExecution:
        """Start workflow, progress to human approval gate, and pause consuming zero tokens."""
        wf_id = f"wf_{uuid.uuid4().hex[:12]}"
        now = datetime.now(UTC)
        payload = initial_payload or {}

        # Step 0: Requirements Analysis checkpoint
        chk_0 = WorkflowCheckpoint(
            id=f"chk_{uuid.uuid4().hex[:12]}",
            workflow_id=wf_id,
            step_index=0,
            node_name=WorkflowNode.REQUIREMENTS_ANALYSIS,
            state_payload={"requirement_id": requirement_id, **payload},
            created_at=now,
        )
        self._checkpoints.save_checkpoint(org_id, chk_0)
        self._broker.publish(
            org_id,
            WorkflowEvent(
                id=f"evt_{uuid.uuid4().hex[:12]}",
                workflow_id=wf_id,
                event_type=WorkflowEventType.NODE_TRANSITION,
                node_name=WorkflowNode.REQUIREMENTS_ANALYSIS,
                payload={"step": 0},
                timestamp=now,
            ),
        )

        # Step 1: Planning and Budget checkpoint
        chk_1 = WorkflowCheckpoint(
            id=f"chk_{uuid.uuid4().hex[:12]}",
            workflow_id=wf_id,
            step_index=1,
            node_name=WorkflowNode.PLANNING_AND_BUDGET,
            state_payload={"plan_id": plan_id, "budget_allocated": True},
            created_at=now,
        )
        self._checkpoints.save_checkpoint(org_id, chk_1)
        self._broker.publish(
            org_id,
            WorkflowEvent(
                id=f"evt_{uuid.uuid4().hex[:12]}",
                workflow_id=wf_id,
                event_type=WorkflowEventType.TOKEN_USAGE,
                node_name=WorkflowNode.PLANNING_AND_BUDGET,
                payload={"tokens_used": 1200, "cost_usd": 0.02},
                timestamp=now,
            ),
        )

        # Step 2: Awaiting Human Approval checkpoint
        chk_2 = WorkflowCheckpoint(
            id=f"chk_{uuid.uuid4().hex[:12]}",
            workflow_id=wf_id,
            step_index=2,
            node_name=WorkflowNode.AWAITING_HUMAN_APPROVAL,
            state_payload={"approval_requested": True},
            created_at=now,
        )
        self._checkpoints.save_checkpoint(org_id, chk_2)
        self._broker.publish(
            org_id,
            WorkflowEvent(
                id=f"evt_{uuid.uuid4().hex[:12]}",
                workflow_id=wf_id,
                event_type=WorkflowEventType.APPROVAL_REQUESTED,
                node_name=WorkflowNode.AWAITING_HUMAN_APPROVAL,
                payload={"state": "awaiting_approval"},
                timestamp=now,
            ),
        )

        execution = WorkflowExecution(
            id=wf_id,
            requirement_id=requirement_id,
            plan_id=plan_id,
            current_node=WorkflowNode.AWAITING_HUMAN_APPROVAL,
            state=WorkflowState.AWAITING_APPROVAL,
            step_count=3,
            actor_id=actor_id,
            created_at=now,
            updated_at=now,
        )

        self._executions[(org_id, wf_id)] = execution
        return execution

    def get_workflow(self, org_id: UUID, workflow_id: str) -> WorkflowExecution:
        """Fetch an active workflow execution by ID within tenant."""
        execution = self._executions.get((org_id, workflow_id))
        if not execution:
            raise WorkflowNotFoundError(f"Workflow '{workflow_id}' not found in organization.")
        return execution

    def send_signal(
        self,
        org_id: UUID,
        workflow_id: str,
        signal_name: str,
        payload: dict[str, Any] | None = None,
        actor_id: str = "system",
    ) -> WorkflowExecution:
        """Deliver an external signal to advance, pause, or resume workflow execution."""
        execution = self.get_workflow(org_id, workflow_id)
        now = datetime.now(UTC)
        sig = signal_name.lower()

        if sig == "approve":
            if execution.state != WorkflowState.AWAITING_APPROVAL:
                raise InvalidWorkflowStateTransitionError(
                    f"Cannot approve workflow in '{execution.state}' state."
                )

            # Advance to Execution Dispatch
            chk_3 = WorkflowCheckpoint(
                id=f"chk_{uuid.uuid4().hex[:12]}",
                workflow_id=workflow_id,
                step_index=execution.step_count,
                node_name=WorkflowNode.EXECUTION_DISPATCH,
                state_payload={"approved_by": actor_id, "signal_payload": payload or {}},
                created_at=now,
            )
            self._checkpoints.save_checkpoint(org_id, chk_3)
            self._broker.publish(
                org_id,
                WorkflowEvent(
                    id=f"evt_{uuid.uuid4().hex[:12]}",
                    workflow_id=workflow_id,
                    event_type=WorkflowEventType.NODE_TRANSITION,
                    node_name=WorkflowNode.EXECUTION_DISPATCH,
                    payload={"step": execution.step_count},
                    timestamp=now,
                ),
            )

            # Advance to Verification & Testing
            chk_4 = WorkflowCheckpoint(
                id=f"chk_{uuid.uuid4().hex[:12]}",
                workflow_id=workflow_id,
                step_index=execution.step_count + 1,
                node_name=WorkflowNode.VERIFICATION_AND_TESTING,
                state_payload={"testing_passed": True},
                created_at=now,
            )
            self._checkpoints.save_checkpoint(org_id, chk_4)
            self._broker.publish(
                org_id,
                WorkflowEvent(
                    id=f"evt_{uuid.uuid4().hex[:12]}",
                    workflow_id=workflow_id,
                    event_type=WorkflowEventType.TOKEN_USAGE,
                    node_name=WorkflowNode.VERIFICATION_AND_TESTING,
                    payload={"tokens_used": 6800, "cost_usd": 0.12},
                    timestamp=now,
                ),
            )

            # Advance to Review & Signoff
            chk_5 = WorkflowCheckpoint(
                id=f"chk_{uuid.uuid4().hex[:12]}",
                workflow_id=workflow_id,
                step_index=execution.step_count + 2,
                node_name=WorkflowNode.REVIEW_AND_SIGNOFF,
                state_payload={"signoff_ready": True},
                created_at=now,
            )
            self._checkpoints.save_checkpoint(org_id, chk_5)
            self._broker.publish(
                org_id,
                WorkflowEvent(
                    id=f"evt_{uuid.uuid4().hex[:12]}",
                    workflow_id=workflow_id,
                    event_type=WorkflowEventType.STATUS_CHANGE,
                    node_name=WorkflowNode.REVIEW_AND_SIGNOFF,
                    payload={"state": "completed"},
                    timestamp=now,
                ),
            )

            updated = WorkflowExecution(
                id=execution.id,
                requirement_id=execution.requirement_id,
                plan_id=execution.plan_id,
                current_node=WorkflowNode.REVIEW_AND_SIGNOFF,
                state=WorkflowState.COMPLETED,
                step_count=execution.step_count + 3,
                actor_id=actor_id,
                created_at=execution.created_at,
                updated_at=now,
            )
            self._executions[(org_id, workflow_id)] = updated
            return updated

        if sig == "reject":
            self._broker.publish(
                org_id,
                WorkflowEvent(
                    id=f"evt_{uuid.uuid4().hex[:12]}",
                    workflow_id=workflow_id,
                    event_type=WorkflowEventType.STATUS_CHANGE,
                    node_name=execution.current_node,
                    payload={"state": "cancelled"},
                    timestamp=now,
                ),
            )
            updated = WorkflowExecution(
                id=execution.id,
                requirement_id=execution.requirement_id,
                plan_id=execution.plan_id,
                current_node=execution.current_node,
                state=WorkflowState.CANCELLED,
                step_count=execution.step_count,
                actor_id=actor_id,
                created_at=execution.created_at,
                updated_at=now,
            )
            self._executions[(org_id, workflow_id)] = updated
            return updated

        if sig == "interrupt":
            self._broker.publish(
                org_id,
                WorkflowEvent(
                    id=f"evt_{uuid.uuid4().hex[:12]}",
                    workflow_id=workflow_id,
                    event_type=WorkflowEventType.STATUS_CHANGE,
                    node_name=execution.current_node,
                    payload={"state": "paused"},
                    timestamp=now,
                ),
            )
            updated = WorkflowExecution(
                id=execution.id,
                requirement_id=execution.requirement_id,
                plan_id=execution.plan_id,
                current_node=execution.current_node,
                state=WorkflowState.PAUSED,
                step_count=execution.step_count,
                actor_id=actor_id,
                created_at=execution.created_at,
                updated_at=now,
            )
            self._executions[(org_id, workflow_id)] = updated
            return updated

        if sig == "resume":
            if execution.state != WorkflowState.PAUSED:
                raise InvalidWorkflowStateTransitionError(
                    f"Cannot resume workflow in '{execution.state}' state."
                )
            target_state = (
                WorkflowState.AWAITING_APPROVAL
                if execution.current_node == WorkflowNode.AWAITING_HUMAN_APPROVAL
                else WorkflowState.RUNNING
            )
            self._broker.publish(
                org_id,
                WorkflowEvent(
                    id=f"evt_{uuid.uuid4().hex[:12]}",
                    workflow_id=workflow_id,
                    event_type=WorkflowEventType.STATUS_CHANGE,
                    node_name=execution.current_node,
                    payload={"state": target_state.value},
                    timestamp=now,
                ),
            )
            updated = WorkflowExecution(
                id=execution.id,
                requirement_id=execution.requirement_id,
                plan_id=execution.plan_id,
                current_node=execution.current_node,
                state=target_state,
                step_count=execution.step_count,
                actor_id=actor_id,
                created_at=execution.created_at,
                updated_at=now,
            )
            self._executions[(org_id, workflow_id)] = updated
            return updated

        raise InvalidWorkflowStateTransitionError(f"Unknown signal '{signal_name}'.")

    def list_checkpoints(self, org_id: UUID, workflow_id: str) -> list[WorkflowCheckpoint]:
        """Fetch all historical checkpoints for a workflow."""
        # Ensure workflow exists
        self.get_workflow(org_id, workflow_id)
        return self._checkpoints.list_checkpoints(org_id, workflow_id)

    def rollback_to_checkpoint(
        self, org_id: UUID, workflow_id: str, checkpoint_id: str
    ) -> WorkflowExecution:
        """Restore workflow state to a previous immutable checkpoint."""
        execution = self.get_workflow(org_id, workflow_id)
        chk = self._checkpoints.get_checkpoint(org_id, workflow_id, checkpoint_id)
        now = datetime.now(UTC)

        target_state = (
            WorkflowState.AWAITING_APPROVAL
            if chk.node_name == WorkflowNode.AWAITING_HUMAN_APPROVAL
            else WorkflowState.RUNNING
        )

        updated = WorkflowExecution(
            id=execution.id,
            requirement_id=execution.requirement_id,
            plan_id=execution.plan_id,
            current_node=chk.node_name,
            state=target_state,
            step_count=chk.step_index + 1,
            actor_id=execution.actor_id,
            created_at=execution.created_at,
            updated_at=now,
        )

        self._executions[(org_id, workflow_id)] = updated
        return updated

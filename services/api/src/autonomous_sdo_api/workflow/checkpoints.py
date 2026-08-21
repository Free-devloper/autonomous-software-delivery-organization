from uuid import UUID

from autonomous_sdo_api.workflow.models import CheckpointNotFoundError, WorkflowCheckpoint


class CheckpointStore:
    """Manages append-only immutable state checkpoints per tenant organization."""

    def __init__(self) -> None:
        # Storage keyed by (org_id, workflow_id) -> list[WorkflowCheckpoint]
        self._checkpoints: dict[tuple[UUID, str], list[WorkflowCheckpoint]] = {}

    def save_checkpoint(self, org_id: UUID, checkpoint: WorkflowCheckpoint) -> None:
        """Persist a new immutable checkpoint."""
        key = (org_id, checkpoint.workflow_id)
        self._checkpoints.setdefault(key, []).append(checkpoint)

    def get_checkpoint(
        self, org_id: UUID, workflow_id: str, checkpoint_id: str
    ) -> WorkflowCheckpoint:
        """Retrieve a specific checkpoint by ID."""
        key = (org_id, workflow_id)
        chk_list = self._checkpoints.get(key, [])
        for chk in chk_list:
            if chk.id == checkpoint_id:
                return chk
        raise CheckpointNotFoundError(
            f"Checkpoint '{checkpoint_id}' not found for workflow '{workflow_id}'."
        )

    def list_checkpoints(self, org_id: UUID, workflow_id: str) -> list[WorkflowCheckpoint]:
        """Fetch all historical checkpoints for a workflow."""
        key = (org_id, workflow_id)
        return list(self._checkpoints.get(key, []))

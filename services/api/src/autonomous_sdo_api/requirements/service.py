import uuid
from datetime import UTC, datetime
from uuid import UUID

from autonomous_sdo_api.requirements.models import (
    AcceptanceCriterion,
    ClarificationNotFoundError,
    ClarificationRequest,
    ClarificationStatus,
    RequirementNotFoundError,
    RequirementRevision,
    RequirementStatus,
)


class RequirementLifecycleService:
    """Manages immutable requirement revisions, criteria, and interactive clarifications."""

    def __init__(self) -> None:
        # Storage keyed by (org_id, requirement_id) -> list[RequirementRevision]
        self._revisions: dict[tuple[UUID, str], list[RequirementRevision]] = {}
        # Storage keyed by (org_id, requirement_id) -> list[ClarificationRequest]
        self._clarifications: dict[tuple[UUID, str], list[ClarificationRequest]] = {}

    def create_requirement(
        self,
        org_id: UUID,
        title: str,
        description: str,
        scope: str,
        criteria: list[AcceptanceCriterion],
        author_id: str,
    ) -> RequirementRevision:
        """Create a new requirement with initial version 1."""
        req_id = f"req_{uuid.uuid4().hex[:12]}"
        rev_id = f"rev_{uuid.uuid4().hex[:12]}"
        now = datetime.now(UTC)

        rev = RequirementRevision(
            id=rev_id,
            requirement_id=req_id,
            version=1,
            title=title,
            description=description,
            scope=scope,
            acceptance_criteria=criteria,
            status=RequirementStatus.DRAFT,
            author_id=author_id,
            created_at=now,
        )

        self._revisions[(org_id, req_id)] = [rev]
        self._clarifications[(org_id, req_id)] = []
        return rev

    def create_revision(
        self,
        org_id: UUID,
        requirement_id: str,
        title: str,
        description: str,
        scope: str,
        criteria: list[AcceptanceCriterion],
        author_id: str,
    ) -> RequirementRevision:
        """Create a new immutable revision, bumping version and superseding the previous one."""
        revs = self._revisions.get((org_id, requirement_id))
        if not revs:
            raise RequirementNotFoundError(
                f"Requirement '{requirement_id}' not found in organization."
            )

        prev_rev = revs[-1]
        next_version = prev_rev.version + 1
        now = datetime.now(UTC)

        # Mark previous latest as superseded
        superseded_prev = RequirementRevision(
            id=prev_rev.id,
            requirement_id=prev_rev.requirement_id,
            version=prev_rev.version,
            title=prev_rev.title,
            description=prev_rev.description,
            scope=prev_rev.scope,
            acceptance_criteria=prev_rev.acceptance_criteria,
            status=RequirementStatus.SUPERSEDED,
            author_id=prev_rev.author_id,
            created_at=prev_rev.created_at,
        )
        revs[-1] = superseded_prev

        new_rev_id = f"rev_{uuid.uuid4().hex[:12]}"
        new_rev = RequirementRevision(
            id=new_rev_id,
            requirement_id=requirement_id,
            version=next_version,
            title=title,
            description=description,
            scope=scope,
            acceptance_criteria=criteria,
            status=RequirementStatus.DRAFT,
            author_id=author_id,
            created_at=now,
        )

        revs.append(new_rev)
        return new_rev

    def get_latest_revision(self, org_id: UUID, requirement_id: str) -> RequirementRevision:
        """Fetch the active latest revision for a requirement."""
        revs = self._revisions.get((org_id, requirement_id))
        if not revs:
            raise RequirementNotFoundError(
                f"Requirement '{requirement_id}' not found in organization."
            )
        return revs[-1]

    def list_revisions(self, org_id: UUID, requirement_id: str) -> list[RequirementRevision]:
        """Fetch all immutable historical revisions for a requirement."""
        revs = self._revisions.get((org_id, requirement_id))
        if not revs:
            raise RequirementNotFoundError(
                f"Requirement '{requirement_id}' not found in organization."
            )
        return list(revs)

    def list_all_requirements(self, org_id: UUID) -> list[RequirementRevision]:
        """Fetch the latest revision of all requirements belonging to an organization."""
        results = []
        for (stored_org, _), revs in self._revisions.items():
            if stored_org == org_id and revs:
                results.append(revs[-1])
        return results

    def request_clarification(
        self,
        org_id: UUID,
        requirement_id: str,
        question: str,
        options: list[str],
    ) -> ClarificationRequest:
        """Create a clarification request and mark latest revision as PENDING_CLARIFICATION."""
        revs = self._revisions.get((org_id, requirement_id))
        if not revs:
            raise RequirementNotFoundError(
                f"Requirement '{requirement_id}' not found in organization."
            )

        now = datetime.now(UTC)
        clar_id = f"clar_{uuid.uuid4().hex[:12]}"
        clar = ClarificationRequest(
            id=clar_id,
            requirement_id=requirement_id,
            question=question,
            options=options,
            status=ClarificationStatus.PENDING,
            created_at=now,
        )

        self._clarifications.setdefault((org_id, requirement_id), []).append(clar)

        # Transition latest revision status to pending_clarification
        latest = revs[-1]
        revs[-1] = RequirementRevision(
            id=latest.id,
            requirement_id=latest.requirement_id,
            version=latest.version,
            title=latest.title,
            description=latest.description,
            scope=latest.scope,
            acceptance_criteria=latest.acceptance_criteria,
            status=RequirementStatus.PENDING_CLARIFICATION,
            author_id=latest.author_id,
            created_at=latest.created_at,
        )

        return clar

    def resolve_clarification(
        self,
        org_id: UUID,
        requirement_id: str,
        clarification_id: str,
        response: str,
    ) -> ClarificationRequest:
        """Answer a clarification and restore requirement status when all items are resolved."""
        clars = self._clarifications.get((org_id, requirement_id))
        if clars is None:
            raise RequirementNotFoundError(
                f"Requirement '{requirement_id}' not found in organization."
            )

        target_idx = None
        for idx, c in enumerate(clars):
            if c.id == clarification_id:
                target_idx = idx
                break

        if target_idx is None:
            raise ClarificationNotFoundError(f"Clarification '{clarification_id}' not found.")

        target = clars[target_idx]
        now = datetime.now(UTC)
        resolved_clar = ClarificationRequest(
            id=target.id,
            requirement_id=target.requirement_id,
            question=target.question,
            options=target.options,
            response=response,
            status=ClarificationStatus.RESOLVED,
            created_at=target.created_at,
            resolved_at=now,
        )
        clars[target_idx] = resolved_clar

        # If all clarifications resolved, restore requirement status to draft
        any_pending = any(c.status == ClarificationStatus.PENDING for c in clars)
        if not any_pending:
            revs = self._revisions.get((org_id, requirement_id))
            if revs and revs[-1].status == RequirementStatus.PENDING_CLARIFICATION:
                latest = revs[-1]
                revs[-1] = RequirementRevision(
                    id=latest.id,
                    requirement_id=latest.requirement_id,
                    version=latest.version,
                    title=latest.title,
                    description=latest.description,
                    scope=latest.scope,
                    acceptance_criteria=latest.acceptance_criteria,
                    status=RequirementStatus.DRAFT,
                    author_id=latest.author_id,
                    created_at=latest.created_at,
                )

        return resolved_clar

    def list_clarifications(self, org_id: UUID, requirement_id: str) -> list[ClarificationRequest]:
        """Fetch all clarifications for a requirement."""
        if (org_id, requirement_id) not in self._revisions:
            raise RequirementNotFoundError(
                f"Requirement '{requirement_id}' not found in organization."
            )
        return list(self._clarifications.get((org_id, requirement_id), []))

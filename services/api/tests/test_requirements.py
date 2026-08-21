from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from autonomous_sdo_api.app import create_app
from autonomous_sdo_api.config import Settings
from autonomous_sdo_api.database.tenancy import OrganizationContext, get_organization_context
from autonomous_sdo_api.policy import Role
from autonomous_sdo_api.requirements import (
    AcceptanceCriterion,
    ClarificationNotFoundError,
    ClarificationStatus,
    RequirementLifecycleService,
    RequirementNotFoundError,
    RequirementStatus,
    VerificationMethod,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Requirement Lifecycle Service Unit Tests
# ---------------------------------------------------------------------------


def test_requirement_lifecycle_service() -> None:
    service = RequirementLifecycleService()
    org_id = uuid4()
    author = "usr-lead-1"

    criteria = [
        AcceptanceCriterion(
            id="ac-1",
            criterion_text="Token expiration must be checked on every request.",
            verification_method=VerificationMethod.AUTOMATED_TEST,
            is_mandatory=True,
        )
    ]

    # 1. Create requirement v1
    v1 = service.create_requirement(
        org_id=org_id,
        title="OIDC Auth",
        description="Integrate Keycloak auth",
        scope="services/api/src/auth.py",
        criteria=criteria,
        author_id=author,
    )
    assert v1.version == 1
    assert v1.status == RequirementStatus.DRAFT
    assert len(v1.acceptance_criteria) == 1

    # 2. Get latest
    latest = service.get_latest_revision(org_id, v1.requirement_id)
    assert latest.id == v1.id

    # 3. Create revision v2
    v2 = service.create_revision(
        org_id=org_id,
        requirement_id=v1.requirement_id,
        title="OIDC Auth Updated",
        description="Integrate Keycloak auth with token caching",
        scope="services/api/src/auth.py",
        criteria=criteria,
        author_id=author,
    )
    assert v2.version == 2
    assert v2.status == RequirementStatus.DRAFT

    # Verify history
    history = service.list_revisions(org_id, v1.requirement_id)
    assert len(history) == 2
    assert history[0].version == 1
    assert history[0].status == RequirementStatus.SUPERSEDED
    assert history[1].version == 2

    # 4. Request clarification
    clar = service.request_clarification(
        org_id=org_id,
        requirement_id=v1.requirement_id,
        question="What is the token cache TTL?",
        options=["5 minutes", "15 minutes"],
    )
    assert clar.status == ClarificationStatus.PENDING

    # Latest revision status should now be PENDING_CLARIFICATION
    latest_clar = service.get_latest_revision(org_id, v1.requirement_id)
    assert latest_clar.status == RequirementStatus.PENDING_CLARIFICATION

    # 5. Resolve clarification
    resolved = service.resolve_clarification(
        org_id=org_id,
        requirement_id=v1.requirement_id,
        clarification_id=clar.id,
        response="5 minutes",
    )
    assert resolved.status == ClarificationStatus.RESOLVED
    assert resolved.response == "5 minutes"
    assert resolved.resolved_at is not None

    # Status should be restored to DRAFT
    latest_restored = service.get_latest_revision(org_id, v1.requirement_id)
    assert latest_restored.status == RequirementStatus.DRAFT


def test_requirement_service_errors() -> None:
    service = RequirementLifecycleService()
    org_id = uuid4()

    with pytest.raises(RequirementNotFoundError):
        service.get_latest_revision(org_id, "non-existent")

    with pytest.raises(RequirementNotFoundError):
        service.create_revision(org_id, "non-existent", "t", "d", "s", [], "usr-1")

    with pytest.raises(RequirementNotFoundError):
        service.request_clarification(org_id, "non-existent", "q", [])

    with pytest.raises(RequirementNotFoundError):
        service.list_clarifications(org_id, "non-existent")

    with pytest.raises(RequirementNotFoundError):
        service.resolve_clarification(org_id, "non-existent", "clar-1", "ans")

    # Create one to test clarification not found
    rev = service.create_requirement(
        org_id,
        "Title",
        "Desc",
        "scope",
        [AcceptanceCriterion(id="1", criterion_text="txt")],
        "usr-1",
    )
    with pytest.raises(ClarificationNotFoundError):
        service.resolve_clarification(org_id, rev.requirement_id, "missing-clar", "ans")


def test_requirement_tenant_isolation() -> None:
    service = RequirementLifecycleService()
    org_a = uuid4()
    org_b = uuid4()

    rev_a = service.create_requirement(
        org_id=org_a,
        title="Tenant A Feature",
        description="Tenant A only",
        scope="apps/web",
        criteria=[AcceptanceCriterion(id="1", criterion_text="txt")],
        author_id="usr-a",
    )

    # Org A sees it
    assert service.get_latest_revision(org_a, rev_a.requirement_id).id == rev_a.id
    assert len(service.list_all_requirements(org_a)) == 1

    # Org B cannot access Org A's requirement
    with pytest.raises(RequirementNotFoundError):
        service.get_latest_revision(org_b, rev_a.requirement_id)
    assert len(service.list_all_requirements(org_b)) == 0


# ---------------------------------------------------------------------------
# Requirement API Route Tests
# ---------------------------------------------------------------------------


def test_requirement_api_routes() -> None:
    settings = Settings(service_name="asdo-reqs-test")
    app = create_app(settings=settings)
    client = TestClient(app)
    org_id = UUID("018f0000-0000-7000-8000-000000000001")

    # Override org context for Maintainer
    app.dependency_overrides[get_organization_context] = lambda: OrganizationContext(
        organization_id=org_id,
        actor_id="usr-req-1",
        roles=frozenset({Role.REPOSITORY_MAINTAINER}),
    )

    # 1. Create requirement
    res_create = client.post(
        "/api/v1/requirements",
        json={
            "title": "ArgoCD Rollout Strategy",
            "description": "Implement canary deployment strategies",
            "scope": "infra/argocd",
            "acceptance_criteria": [
                {
                    "id": "ac-1",
                    "criterion_text": "Canary step increments by 20%",
                    "verification_method": "automated_test",
                    "is_mandatory": True,
                }
            ],
        },
    )
    assert res_create.status_code == 201
    req_data = res_create.json()
    req_id = req_data["requirement_id"]
    assert req_data["version"] == 1
    assert req_data["title"] == "ArgoCD Rollout Strategy"

    # 2. List requirements
    res_list = client.get("/api/v1/requirements")
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    # 3. Get single requirement
    res_get = client.get(f"/api/v1/requirements/{req_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == req_data["id"]

    # 4. Create revision v2
    res_rev = client.post(
        f"/api/v1/requirements/{req_id}/revisions",
        json={
            "title": "ArgoCD Rollout Strategy v2",
            "description": "Updated rollout with metric analysis",
            "scope": "infra/argocd",
            "acceptance_criteria": [
                {
                    "id": "ac-1",
                    "criterion_text": "Prometheus metric analysis on rollout",
                    "verification_method": "automated_test",
                    "is_mandatory": True,
                }
            ],
        },
    )
    assert res_rev.status_code == 201
    assert res_rev.json()["version"] == 2

    # 5. List revisions
    res_revs = client.get(f"/api/v1/requirements/{req_id}/revisions")
    assert res_revs.status_code == 200
    assert len(res_revs.json()) == 2

    # 6. Request clarification
    res_clar = client.post(
        f"/api/v1/requirements/{req_id}/clarifications",
        json={
            "question": "Which Prometheus metric should govern rollback?",
            "options": ["http_requests_total error rate", "request_duration_seconds"],
        },
    )
    assert res_clar.status_code == 201
    clar_id = res_clar.json()["id"]

    # 7. List clarifications
    res_clars = client.get(f"/api/v1/requirements/{req_id}/clarifications")
    assert res_clars.status_code == 200
    assert len(res_clars.json()) == 1

    # 8. Resolve clarification
    res_resolve = client.post(
        f"/api/v1/requirements/{req_id}/clarifications/{clar_id}/resolve",
        json={"response": "http_requests_total error rate"},
    )
    assert res_resolve.status_code == 200
    assert res_resolve.json()["status"] == "resolved"


def test_requirements_rbac_authorization() -> None:
    settings = Settings(service_name="asdo-reqs-rbac-test")
    app = create_app(settings=settings)
    client = TestClient(app)
    org_id = UUID("018f0000-0000-7000-8000-000000000001")

    # Read-only viewer role
    app.dependency_overrides[get_organization_context] = lambda: OrganizationContext(
        organization_id=org_id,
        actor_id="usr-viewer-1",
        roles=frozenset({Role.READ_ONLY_VIEWER}),
    )

    # Creation should be forbidden (403)
    res = client.post(
        "/api/v1/requirements",
        json={
            "title": "Unauthorized Requirement",
            "description": "Should fail with 403",
            "scope": "",
            "acceptance_criteria": [
                {
                    "id": "1",
                    "criterion_text": "Text",
                    "verification_method": "automated_test",
                }
            ],
        },
    )
    assert res.status_code == 403

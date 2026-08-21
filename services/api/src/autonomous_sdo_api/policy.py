"""Deterministic role policy for Phase 0C protected API actions."""

from __future__ import annotations

from enum import StrEnum

from fastapi import HTTPException, status


class Role(StrEnum):
    ORGANIZATION_OWNER = "organization_owner"
    ORGANIZATION_ADMINISTRATOR = "organization_administrator"
    REPOSITORY_ADMINISTRATOR = "repository_administrator"
    REQUESTER = "requester"
    REPOSITORY_MAINTAINER = "repository_maintainer"
    SECURITY_REVIEWER = "security_reviewer"
    RELEASE_MANAGER = "release_manager"
    RUN_OPERATOR = "run_operator"
    AUDITOR = "auditor"
    BILLING_ADMINISTRATOR = "billing_administrator"
    READ_ONLY_VIEWER = "read_only_viewer"
    SERVICE_ACCOUNT = "service_account"


class Action(StrEnum):
    READ_ORGANIZATION_CONFIGURATION = "organization.configuration.read"
    READ_REPOSITORY = "repository.read"
    READ_REQUIREMENTS = "requirements.read"
    MANAGE_REQUIREMENTS = "requirements.manage"
    READ_PLANS = "planning.plans.read"
    MANAGE_PLANS = "planning.plans.manage"
    READ_WORKFLOWS = "workflows.read"
    MANAGE_WORKFLOWS = "workflows.manage"


_ACTION_ROLES: dict[Action, frozenset[Role]] = {
    Action.READ_ORGANIZATION_CONFIGURATION: frozenset(
        {
            Role.ORGANIZATION_OWNER,
            Role.ORGANIZATION_ADMINISTRATOR,
            Role.AUDITOR,
            Role.READ_ONLY_VIEWER,
            Role.SERVICE_ACCOUNT,
        }
    ),
    Action.READ_REPOSITORY: frozenset(
        {
            Role.ORGANIZATION_OWNER,
            Role.ORGANIZATION_ADMINISTRATOR,
            Role.REPOSITORY_ADMINISTRATOR,
            Role.REPOSITORY_MAINTAINER,
            Role.REQUESTER,
            Role.SECURITY_REVIEWER,
            Role.RELEASE_MANAGER,
            Role.RUN_OPERATOR,
            Role.AUDITOR,
            Role.READ_ONLY_VIEWER,
            Role.SERVICE_ACCOUNT,
        }
    ),
    Action.READ_REQUIREMENTS: frozenset(
        {
            Role.ORGANIZATION_OWNER,
            Role.ORGANIZATION_ADMINISTRATOR,
            Role.REPOSITORY_ADMINISTRATOR,
            Role.REPOSITORY_MAINTAINER,
            Role.REQUESTER,
            Role.SECURITY_REVIEWER,
            Role.RELEASE_MANAGER,
            Role.RUN_OPERATOR,
            Role.AUDITOR,
            Role.READ_ONLY_VIEWER,
            Role.SERVICE_ACCOUNT,
        }
    ),
    Action.MANAGE_REQUIREMENTS: frozenset(
        {
            Role.ORGANIZATION_OWNER,
            Role.ORGANIZATION_ADMINISTRATOR,
            Role.REPOSITORY_ADMINISTRATOR,
            Role.REPOSITORY_MAINTAINER,
            Role.REQUESTER,
            Role.SERVICE_ACCOUNT,
        }
    ),
    Action.READ_PLANS: frozenset(
        {
            Role.ORGANIZATION_OWNER,
            Role.ORGANIZATION_ADMINISTRATOR,
            Role.REPOSITORY_ADMINISTRATOR,
            Role.REPOSITORY_MAINTAINER,
            Role.REQUESTER,
            Role.SECURITY_REVIEWER,
            Role.RELEASE_MANAGER,
            Role.RUN_OPERATOR,
            Role.AUDITOR,
            Role.READ_ONLY_VIEWER,
            Role.SERVICE_ACCOUNT,
        }
    ),
    Action.MANAGE_PLANS: frozenset(
        {
            Role.ORGANIZATION_OWNER,
            Role.ORGANIZATION_ADMINISTRATOR,
            Role.REPOSITORY_ADMINISTRATOR,
            Role.REPOSITORY_MAINTAINER,
            Role.REQUESTER,
            Role.SERVICE_ACCOUNT,
        }
    ),
    Action.READ_WORKFLOWS: frozenset(
        {
            Role.ORGANIZATION_OWNER,
            Role.ORGANIZATION_ADMINISTRATOR,
            Role.REPOSITORY_ADMINISTRATOR,
            Role.REPOSITORY_MAINTAINER,
            Role.REQUESTER,
            Role.SECURITY_REVIEWER,
            Role.RELEASE_MANAGER,
            Role.RUN_OPERATOR,
            Role.AUDITOR,
            Role.READ_ONLY_VIEWER,
            Role.SERVICE_ACCOUNT,
        }
    ),
    Action.MANAGE_WORKFLOWS: frozenset(
        {
            Role.ORGANIZATION_OWNER,
            Role.ORGANIZATION_ADMINISTRATOR,
            Role.REPOSITORY_ADMINISTRATOR,
            Role.REPOSITORY_MAINTAINER,
            Role.RUN_OPERATOR,
            Role.SERVICE_ACCOUNT,
        }
    ),
}


class AuthorizationPolicy:
    """Deny-by-default authorization that never consults model output."""

    def require(self, actor_roles: frozenset[Role], action: Action) -> None:
        allowed_roles = _ACTION_ROLES.get(action, frozenset())
        if actor_roles.isdisjoint(allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The authenticated actor is not authorized for this action.",
            )

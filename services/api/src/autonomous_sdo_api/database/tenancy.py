"""Tenant context primitives that deliberately fail closed without identity."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from fastapi import Header, HTTPException, Request, status

from autonomous_sdo_api.auth import AuthenticationError, OidcTokenVerifier
from autonomous_sdo_api.policy import Role


@dataclass(frozen=True, slots=True)
class OrganizationContext:
    """Verified organization identity passed from the future authentication boundary."""

    organization_id: UUID
    actor_id: str = "system"
    roles: frozenset[Role] = field(default_factory=frozenset)


async def get_organization_context(
    request: Request,
    authorization: str | None = Header(default=None),
    organization_header: str | None = Header(default=None, alias="X-ASDO-Organization-ID"),
) -> OrganizationContext:
    """Resolve the active organization from a verified bearer token and explicit header."""
    verifier = getattr(request.app.state, "oidc_token_verifier", None)
    if not isinstance(verifier, OidcTokenVerifier):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Organization identity is unavailable until authentication is configured.",
        )
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer authentication is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if organization_header is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-ASDO-Organization-ID is required.",
        )
    try:
        organization_id = UUID(organization_header)
        principal = verifier.verify(authorization.removeprefix("Bearer ").strip())
    except (AuthenticationError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token is invalid.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
    organization = principal.organizations.get(organization_id)
    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The authenticated actor is not a member of the requested organization.",
        )
    return OrganizationContext(
        organization_id=organization_id,
        actor_id=principal.subject,
        roles=organization.roles,
    )

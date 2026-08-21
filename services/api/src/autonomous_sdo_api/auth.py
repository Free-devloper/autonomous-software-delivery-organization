"""OIDC bearer-token verification and organization-claim extraction."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from uuid import UUID

import jwt
from jwt import InvalidTokenError, PyJWK

from .policy import Role


class AuthenticationError(ValueError):
    """Raised when token verification or claim extraction fails closed."""


@dataclass(frozen=True, slots=True)
class AuthenticatedOrganization:
    organization_id: UUID
    roles: frozenset[Role]


@dataclass(frozen=True, slots=True)
class AuthenticatedPrincipal:
    subject: str
    organizations: Mapping[UUID, AuthenticatedOrganization]


class OidcTokenVerifier:
    """Verify RS256 OIDC access tokens against configured issuer, audience and JWKS."""

    def __init__(
        self,
        *,
        issuer: str,
        audience: str,
        jwks: Mapping[str, Any],
        organization_claim: str,
    ) -> None:
        self._issuer = issuer
        self._audience = audience
        self._organization_claim = organization_claim
        self._keys_by_kid = self._build_key_map(jwks)

    def verify(self, token: str) -> AuthenticatedPrincipal:
        try:
            header = jwt.get_unverified_header(token)
            key = self._find_key(str(header.get("kid", "")))
            claims = jwt.decode(
                token,
                key=key,
                algorithms=["RS256"],
                audience=self._audience,
                issuer=self._issuer,
                options={"require": ["aud", "exp", "iat", "iss", "sub"]},
            )
        except InvalidTokenError as error:
            raise AuthenticationError("Bearer token is invalid.") from error

        if not isinstance(claims, dict):
            raise AuthenticationError("Bearer token claims are invalid.")
        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject:
            raise AuthenticationError("Bearer token subject is invalid.")
        return AuthenticatedPrincipal(
            subject=subject,
            organizations=self._parse_organizations(claims),
        )

    def has_usable_signing_key(self) -> bool:
        return bool(self._keys_by_kid)

    def _build_key_map(self, jwks: Mapping[str, Any]) -> dict[str, Any]:
        keys = jwks.get("keys")
        if not isinstance(keys, list) or not keys:
            return {}
        parsed_keys: dict[str, Any] = {}
        for candidate in keys:
            if not isinstance(candidate, dict):
                continue
            if candidate.get("use") not in {None, "sig"}:
                continue
            if candidate.get("kty") != "RSA":
                continue
            kid = candidate.get("kid")
            if not isinstance(kid, str) or not kid:
                return {}
            if kid in parsed_keys:
                return {}
            try:
                parsed_keys[kid] = PyJWK(candidate, algorithm="RS256").key
            except Exception:
                return {}
        return parsed_keys

    def _find_key(self, kid: str) -> Any:
        key = self._keys_by_kid.get(kid)
        if key is not None:
            return key
        if not self._keys_by_kid:
            raise AuthenticationError("OIDC JWKS is invalid.")
        raise AuthenticationError("Bearer token signing key is not trusted.")

    def _parse_organizations(
        self, claims: Mapping[str, object]
    ) -> dict[UUID, AuthenticatedOrganization]:
        raw_organizations = claims.get(self._organization_claim)
        if not isinstance(raw_organizations, dict):
            raise AuthenticationError("Bearer token does not contain organization access.")
        organizations: dict[UUID, AuthenticatedOrganization] = {}
        for raw_organization_id, raw_roles in raw_organizations.items():
            if not isinstance(raw_organization_id, str) or not isinstance(raw_roles, list):
                raise AuthenticationError("Organization claim shape is invalid.")
            try:
                organization_id = UUID(raw_organization_id)
                roles = frozenset(Role(role) for role in raw_roles if isinstance(role, str))
            except ValueError as error:
                raise AuthenticationError(
                    "Organization claim contains an invalid value."
                ) from error
            if not roles:
                raise AuthenticationError("Organization claim contains no recognized roles.")
            organizations[organization_id] = AuthenticatedOrganization(
                organization_id=organization_id,
                roles=roles,
            )
        if not organizations:
            raise AuthenticationError("Bearer token grants no organization access.")
        return organizations

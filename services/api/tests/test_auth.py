from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from starlette.requests import Request

from autonomous_sdo_api.app import create_app
from autonomous_sdo_api.auth import AuthenticationError, OidcTokenVerifier
from autonomous_sdo_api.config import Settings
from autonomous_sdo_api.database.tenancy import get_organization_context
from autonomous_sdo_api.policy import Action, AuthorizationPolicy, Role

pytestmark = pytest.mark.unit


def _key_material() -> tuple[Any, dict[str, list[dict[str, object]]]]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(private_key.public_key()))
    jwk.update({"kid": "phase-0c-key", "alg": "RS256", "use": "sig"})
    return private_key, {"keys": [jwk]}


def _token(
    private_key: Any,
    *,
    organization_id: UUID,
    roles: list[str],
    audience: str = "asdo-api",
    issuer: str = "https://idp.example.test/realms/asdo",
    kid: str = "phase-0c-key",
) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "iss": issuer,
            "aud": audience,
            "sub": "user-123",
            "iat": now,
            "exp": now + timedelta(minutes=5),
            "asdo_organizations": {str(organization_id): roles},
        },
        private_key,
        algorithm="RS256",
        headers={"kid": kid},
    )


def _verifier(jwks: Mapping[str, Any]) -> OidcTokenVerifier:
    return OidcTokenVerifier(
        issuer="https://idp.example.test/realms/asdo",
        audience="asdo-api",
        jwks=jwks,
        organization_claim="asdo_organizations",
    )


def test_oidc_verifier_accepts_trusted_key_and_extracts_organization_roles() -> None:
    private_key, jwks = _key_material()
    organization_id = UUID("018f4b9d-4c5d-7abc-8def-0123456789ab")

    principal = _verifier(jwks).verify(
        _token(
            private_key,
            organization_id=organization_id,
            roles=[Role.ORGANIZATION_OWNER.value, Role.AUDITOR.value],
        )
    )

    assert principal.subject == "user-123"
    assert principal.organizations[organization_id].roles == frozenset(
        {Role.ORGANIZATION_OWNER, Role.AUDITOR}
    )


@pytest.mark.parametrize(
    "token_overrides",
    [
        {"audience": "other-api"},
        {"issuer": "https://evil.example.test/realms/asdo"},
        {"kid": "unknown-key"},
    ],
)
def test_oidc_verifier_rejects_wrong_token_context(token_overrides: dict[str, str]) -> None:
    private_key, jwks = _key_material()
    organization_id = UUID("018f4b9d-4c5d-7abc-8def-0123456789ab")

    with pytest.raises(AuthenticationError):
        _verifier(jwks).verify(
            _token(
                private_key,
                organization_id=organization_id,
                roles=[Role.ORGANIZATION_OWNER.value],
                **token_overrides,
            )
        )


def test_oidc_verifier_rejects_unknown_roles_and_missing_organization_access() -> None:
    private_key, jwks = _key_material()
    organization_id = UUID("018f4b9d-4c5d-7abc-8def-0123456789ab")

    with pytest.raises(AuthenticationError):
        _verifier(jwks).verify(
            _token(private_key, organization_id=organization_id, roles=["superuser"])
        )


def test_oidc_verifier_reports_usable_signing_key_state() -> None:
    _, jwks = _key_material()
    valid_key = dict(jwks["keys"][0])
    missing_kid = dict(valid_key)
    missing_kid.pop("kid")
    malformed_duplicate = {"kid": valid_key["kid"], "kty": "RSA"}

    assert _verifier(jwks).has_usable_signing_key() is True
    assert _verifier({"keys": []}).has_usable_signing_key() is False
    assert _verifier({"keys": [missing_kid]}).has_usable_signing_key() is False
    assert _verifier({"keys": [valid_key, valid_key]}).has_usable_signing_key() is False
    assert _verifier({"keys": [malformed_duplicate, valid_key]}).has_usable_signing_key() is False
    assert (
        _verifier(
            {"keys": [{"kid": "enc-key", "kty": "RSA", "use": "enc"}]}
        ).has_usable_signing_key()
        is False
    )
    assert _verifier({"keys": [{"kid": "bad-key", "kty": "RSA"}]}).has_usable_signing_key() is False
    assert _verifier({"keys": [{"kid": "ec-key", "kty": "EC"}]}).has_usable_signing_key() is False
    assert _verifier({"keys": "not-a-list"}).has_usable_signing_key() is False


def test_oidc_verifier_rejects_unusable_jwks_without_server_error() -> None:
    private_key, jwks = _key_material()
    organization_id = UUID("018f4b9d-4c5d-7abc-8def-0123456789ab")
    valid_key = dict(jwks["keys"][0])
    malformed_duplicate = {"kid": valid_key["kid"], "kty": "RSA"}

    with pytest.raises(AuthenticationError, match="OIDC JWKS is invalid"):
        _verifier({"keys": [malformed_duplicate, valid_key]}).verify(
            _token(
                private_key,
                organization_id=organization_id,
                roles=[Role.ORGANIZATION_OWNER.value],
            )
        )


def test_authorization_policy_allows_only_configured_roles_for_actions() -> None:
    policy = AuthorizationPolicy()

    policy.require(
        frozenset({Role.READ_ONLY_VIEWER}),
        Action.READ_ORGANIZATION_CONFIGURATION,
    )

    with pytest.raises(Exception) as error:
        policy.require(
            frozenset({Role.REQUESTER}),
            Action.READ_ORGANIZATION_CONFIGURATION,
        )
    assert "not authorized" in str(error.value)


def test_organization_context_requires_matching_bearer_token_and_header() -> None:
    private_key, jwks = _key_material()
    organization_id = UUID("018f4b9d-4c5d-7abc-8def-0123456789ab")
    app = create_app(
        Settings(
            service_name="api-test",
            oidc_issuer="https://idp.example.test/realms/asdo",
            oidc_audience="asdo-api",
            oidc_jwks=jwks,
        )
    )
    request = Request({"type": "http", "app": app})
    token = _token(
        private_key,
        organization_id=organization_id,
        roles=[Role.READ_ONLY_VIEWER.value],
    )

    context = asyncio.run(
        get_organization_context(
            request,
            authorization=f"Bearer {token}",
            organization_header=str(organization_id),
        )
    )

    assert context.organization_id == organization_id
    assert context.actor_id == "user-123"
    assert context.roles == frozenset({Role.READ_ONLY_VIEWER})

    with pytest.raises(HTTPException) as error:
        asyncio.run(
            get_organization_context(
                request,
                authorization=f"Bearer {token}",
                organization_header=str(UUID("018f4b9d-4c5d-7abc-8def-000000000000")),
            )
        )
    assert error.value.status_code == 403

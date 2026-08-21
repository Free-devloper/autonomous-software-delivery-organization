"""FastAPI application factory and versioned routing."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, status

from .auth import OidcTokenVerifier
from .config import Settings, get_settings
from .coordinator.routes import coordinator_router
from .database.audit import AuditEventService
from .database.services import OrganizationConfigurationService
from .database.session import TenantScopedSessionFactory, create_tenant_session_factory
from .database.tenancy import OrganizationContext, get_organization_context
from .deployment.routes import deployment_router
from .evaluation.routes import evaluation_router
from .events.routes import router as events_router
from .patch.routes import patch_router
from .planning.routes import router as planning_router
from .policy import Action, AuthorizationPolicy
from .repository.routes import router as repository_router
from .requirements.routes import router as requirements_router
from .reviews.routes import review_router
from .sandbox.routes import router as sandbox_router
from .schemas import HealthLiveResponse, OrganizationConfigurationResponse
from .security.routes import security_router
from .telemetry import install_telemetry
from .workflow.routes import router as workflow_router

READINESS_DATABASE_TIMEOUT_SECONDS = 2.0


def get_organization_configuration_service(request: Request) -> OrganizationConfigurationService:
    service = getattr(request.app.state, "organization_configuration_service", None)
    if not isinstance(service, OrganizationConfigurationService):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Organization persistence is unavailable.",
        )
    return service


def get_authorization_policy(request: Request) -> AuthorizationPolicy:
    policy = getattr(request.app.state, "authorization_policy", None)
    if not isinstance(policy, AuthorizationPolicy):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authorization policy is unavailable.",
        )
    return policy


def get_audit_event_service(request: Request) -> AuditEventService | None:
    service = getattr(request.app.state, "audit_event_service", None)
    if service is None:
        return None
    if not isinstance(service, AuditEventService):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Audit persistence is unavailable.",
        )
    return service


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Dispose database pools owned by this application when its process stops."""
    try:
        yield
    finally:
        session_factory = getattr(app.state, "tenant_session_factory", None)
        if isinstance(session_factory, TenantScopedSessionFactory):
            await session_factory.close()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create an API application using validated, non-secret runtime settings."""
    active_settings = settings or get_settings()
    app = FastAPI(
        title=active_settings.service_name,
        version="1.0.0",
        openapi_version="3.1.0",
        lifespan=lifespan,
    )
    install_telemetry(app, active_settings)
    if active_settings.database_url is not None:
        session_factory = create_tenant_session_factory(
            active_settings.database_url.get_secret_value()
        )
        app.state.tenant_session_factory = session_factory
        app.state.organization_configuration_service = OrganizationConfigurationService(
            session_factory
        )
        app.state.audit_event_service = AuditEventService(session_factory)
    app.state.authorization_policy = AuthorizationPolicy()
    if active_settings.oidc_configured:
        app.state.oidc_token_verifier = OidcTokenVerifier(
            issuer=active_settings.oidc_issuer or "",
            audience=active_settings.oidc_audience or "",
            jwks=active_settings.oidc_jwks or {},
            organization_claim=active_settings.oidc_organization_claim,
        )

    router = APIRouter(prefix=active_settings.api_v1_prefix, tags=["health"])

    @router.get("/health/live", response_model=HealthLiveResponse, summary="Check process liveness")
    def live_health() -> HealthLiveResponse:
        return HealthLiveResponse(
            status="ok", service=active_settings.service_name, api_version="v1"
        )

    @router.get(
        "/health/ready",
        response_model=HealthLiveResponse,
        summary="Check readiness for protected API traffic",
    )
    async def ready_health(request: Request) -> HealthLiveResponse:
        missing = []
        session_factory = getattr(request.app.state, "tenant_session_factory", None)
        if active_settings.database_url is None or not isinstance(
            session_factory, TenantScopedSessionFactory
        ):
            missing.append("database")
        else:
            try:
                await asyncio.wait_for(
                    session_factory.ping(),
                    timeout=READINESS_DATABASE_TIMEOUT_SECONDS,
                )
            except Exception:
                missing.append("database")

        token_verifier = getattr(request.app.state, "oidc_token_verifier", None)
        if (
            not active_settings.oidc_configured
            or not isinstance(token_verifier, OidcTokenVerifier)
            or not token_verifier.has_usable_signing_key()
        ):
            missing.append("oidc")
        if missing:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"status": "unready", "missing": missing},
            )
        return HealthLiveResponse(
            status="ok", service=active_settings.service_name, api_version="v1"
        )

    @router.get(
        "/organization/configuration",
        response_model=OrganizationConfigurationResponse,
        summary="Read the active organization's residency and classification configuration",
    )
    async def read_organization_configuration(
        context: Annotated[OrganizationContext, Depends(get_organization_context)],
        authorization_policy: Annotated[AuthorizationPolicy, Depends(get_authorization_policy)],
        audit_service: Annotated[AuditEventService | None, Depends(get_audit_event_service)],
        service: Annotated[
            OrganizationConfigurationService,
            Depends(get_organization_configuration_service),
        ],
    ) -> OrganizationConfigurationResponse:
        authorization_policy.require(context.roles, Action.READ_ORGANIZATION_CONFIGURATION)
        configuration = await service.get_for_context(context)
        if audit_service is not None:
            await audit_service.record(
                organization_id=context.organization_id,
                actor_id=context.actor_id,
                action=Action.READ_ORGANIZATION_CONFIGURATION.value,
                resource_type="organization_configuration",
                outcome="success" if configuration is not None else "failure",
                context={"api_version": "v1"},
            )
        if configuration is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
        return OrganizationConfigurationResponse(
            organization_id=configuration.organization_id,
            data_region=configuration.data_region,
            data_classification=configuration.data_classification,
        )

    app.include_router(router)
    app.include_router(repository_router)
    app.include_router(requirements_router)
    app.include_router(planning_router)
    app.include_router(workflow_router)
    app.include_router(events_router)
    app.include_router(sandbox_router)
    app.include_router(patch_router)
    app.include_router(security_router)
    app.include_router(review_router)
    app.include_router(deployment_router)
    app.include_router(evaluation_router)
    app.include_router(coordinator_router)
    return app


app = create_app()

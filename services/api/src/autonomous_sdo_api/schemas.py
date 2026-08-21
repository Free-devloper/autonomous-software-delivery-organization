"""Typed HTTP representations exposed by the API."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints


class HealthLiveResponse(BaseModel):
    """Stable version-one response for process liveness checks."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["ok"]
    service: Annotated[
        str,
        StringConstraints(
            min_length=3,
            max_length=63,
            pattern=r"^[a-z][a-z0-9-]*$",
        ),
    ]
    api_version: Literal["v1"]


class OrganizationConfigurationResponse(BaseModel):
    """Version-one representation of the active organization's persisted configuration."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    organization_id: UUID
    data_region: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=2,
            max_length=63,
            pattern=r"^[a-z][a-z0-9-]*$",
        ),
    ]
    data_classification: Literal["public", "internal", "confidential", "restricted"]

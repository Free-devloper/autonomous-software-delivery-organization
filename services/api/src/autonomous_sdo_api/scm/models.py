import re
from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

COMMIT_SHA_REGEX = r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$"
CommitSha = Annotated[str, StringConstraints(pattern=COMMIT_SHA_REGEX)]


class ScmProvider(StrEnum):
    GITHUB = "github"
    GITLAB = "gitlab"


class RepositoryVisibility(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    PRIVATE = "private"


class WebhookEventType(StrEnum):
    PUSH = "push"
    PULL_REQUEST = "pull_request"
    PING = "ping"


class ScmError(Exception):
    """Base exception for SCM provider operations."""

    def __init__(self, message: str, provider: ScmProvider | str = "unknown") -> None:
        super().__init__(message)
        self.provider = provider


class ScmAuthenticationError(ScmError):
    """Raised when SCM authentication fails or token is invalid/expired."""


class ScmNotFoundError(ScmError):
    """Raised when the requested repository, ref, or file does not exist."""


class ScmRateLimitError(ScmError):
    """Raised when SCM rate limit is exceeded."""

    def __init__(
        self,
        message: str,
        provider: ScmProvider | str = "unknown",
        reset_epoch: int | None = None,
    ) -> None:
        super().__init__(message, provider)
        self.reset_epoch = reset_epoch


class RepositoryDescriptor(BaseModel):
    """Immutable metadata describing a remote repository across providers."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: ScmProvider
    id: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    name: str = Field(min_length=1)
    full_name: str = Field(min_length=1)
    default_branch: str = Field(min_length=1)
    visibility: RepositoryVisibility
    clone_url_http: str
    clone_url_ssh: str = Field(min_length=1)
    is_archived: bool = False


class CommitResolution(BaseModel):
    """Resolved immutable commit with verified SHA hash."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: ScmProvider
    repository_id: str = Field(min_length=1)
    commit_sha: CommitSha
    ref_requested: str | None = None
    message: str
    author_name: str
    author_email: str
    authored_at: datetime
    parent_shas: list[CommitSha] = Field(default_factory=list)

    @classmethod
    def validate_sha(cls, sha: str) -> bool:
        return bool(re.match(COMMIT_SHA_REGEX, sha))


class NormalizedWebhookEvent(BaseModel):
    """Provider-neutral representation of SCM webhook events."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: ScmProvider
    event_id: str = Field(min_length=1)
    event_type: WebhookEventType
    repository_full_name: str = Field(min_length=1)
    ref: str | None = None
    before_sha: CommitSha | None = None
    after_sha: CommitSha | None = None
    pr_number: int | None = None
    action: str | None = None
    sender: str = Field(min_length=1)
    timestamp: datetime

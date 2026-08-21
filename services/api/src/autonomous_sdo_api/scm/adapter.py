from abc import ABC, abstractmethod

from autonomous_sdo_api.scm.models import (
    CommitResolution,
    RepositoryDescriptor,
    ScmProvider,
)


class ScmProviderAdapter(ABC):
    """Abstract interface for interacting with SCM providers (GitHub, GitLab)."""

    @property
    @abstractmethod
    def provider(self) -> ScmProvider:
        """The specific SCM provider identity."""

    @abstractmethod
    async def get_repository(self, owner: str, name: str) -> RepositoryDescriptor:
        """Fetch immutable repository metadata."""

    @abstractmethod
    async def resolve_commit(self, owner: str, name: str, ref: str) -> CommitResolution:
        """Dereference a ref, branch, tag, or short SHA to an immutable full commit SHA."""

    @abstractmethod
    async def get_file_content(self, owner: str, name: str, commit_sha: str, path: str) -> bytes:
        """Retrieve raw file content at a specific immutable commit SHA."""

    @abstractmethod
    async def list_branches(self, owner: str, name: str) -> list[str]:
        """List active branches in the repository."""

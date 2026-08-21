from datetime import datetime
from typing import Any

import httpx

from autonomous_sdo_api.scm.adapter import ScmProviderAdapter
from autonomous_sdo_api.scm.models import (
    CommitResolution,
    RepositoryDescriptor,
    RepositoryVisibility,
    ScmAuthenticationError,
    ScmError,
    ScmNotFoundError,
    ScmProvider,
    ScmRateLimitError,
)


class GitHubAdapter(ScmProviderAdapter):
    """GitHub REST API implementation of ScmProviderAdapter."""

    def __init__(
        self,
        token: str | None = None,
        api_base_url: str = "https://api.github.com",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._token = token
        self._api_base_url = api_base_url.rstrip("/")
        self._client = client
        self._owns_client = client is None

    @property
    def provider(self) -> ScmProvider:
        return ScmProvider.GITHUB

    def _get_headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "ASDO-Autonomous-SDO/1.0",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._api_base_url,
                headers=self._get_headers(),
                timeout=15.0,
            )
        return self._client

    async def close(self) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    def _handle_response_error(self, response: httpx.Response, action_desc: str) -> None:
        if response.is_success:
            return

        status = response.status_code
        if status in (401, 403):
            remaining = response.headers.get("x-ratelimit-remaining")
            if remaining == "0":
                reset_epoch_str = response.headers.get("x-ratelimit-reset")
                reset_epoch = int(reset_epoch_str) if reset_epoch_str else None
                raise ScmRateLimitError(
                    f"GitHub rate limit exceeded during {action_desc}",
                    provider=ScmProvider.GITHUB,
                    reset_epoch=reset_epoch,
                )
            raise ScmAuthenticationError(
                f"GitHub auth failed ({status}) during {action_desc}: {response.text}",
                provider=ScmProvider.GITHUB,
            )
        if status == 404:
            raise ScmNotFoundError(
                f"GitHub resource not found during {action_desc}",
                provider=ScmProvider.GITHUB,
            )
        raise ScmError(
            f"GitHub API error ({status}) during {action_desc}: {response.text}",
            provider=ScmProvider.GITHUB,
        )

    async def get_repository(self, owner: str, name: str) -> RepositoryDescriptor:
        client = self._get_client()
        url = f"/repos/{owner}/{name}"
        response = await client.get(url, headers=self._get_headers())
        self._handle_response_error(response, f"get_repository({owner}/{name})")

        data = response.json()
        visibility = RepositoryVisibility.PRIVATE
        if data.get("visibility") == "public" or data.get("private") is False:
            visibility = RepositoryVisibility.PUBLIC
        elif data.get("visibility") == "internal":
            visibility = RepositoryVisibility.INTERNAL

        return RepositoryDescriptor(
            provider=ScmProvider.GITHUB,
            id=str(data["id"]),
            owner=data["owner"]["login"],
            name=data["name"],
            full_name=data["full_name"],
            default_branch=data["default_branch"],
            visibility=visibility,
            clone_url_http=data["clone_url"],
            clone_url_ssh=data["ssh_url"],
            is_archived=bool(data.get("archived", False)),
        )

    async def resolve_commit(self, owner: str, name: str, ref: str) -> CommitResolution:
        client = self._get_client()
        url = f"/repos/{owner}/{name}/commits/{ref}"
        response = await client.get(url, headers=self._get_headers())
        self._handle_response_error(response, f"resolve_commit({owner}/{name}, {ref})")

        data = response.json()
        commit_sha = data["sha"]
        commit_details = data.get("commit", {})
        author_info = commit_details.get("author", {})
        date_str = author_info.get("date")
        authored_at = datetime.fromisoformat(date_str) if date_str else datetime.now()

        parents = [p["sha"] for p in data.get("parents", []) if "sha" in p]

        return CommitResolution(
            provider=ScmProvider.GITHUB,
            repository_id=f"{owner}/{name}",
            commit_sha=commit_sha,
            ref_requested=ref,
            message=commit_details.get("message", ""),
            author_name=author_info.get("name", "unknown"),
            author_email=author_info.get("email", "unknown"),
            authored_at=authored_at,
            parent_shas=parents,
        )

    async def get_file_content(self, owner: str, name: str, commit_sha: str, path: str) -> bytes:
        client = self._get_client()
        url = f"/repos/{owner}/{name}/contents/{path.lstrip('/')}"
        headers = dict(self._get_headers())
        headers["Accept"] = "application/vnd.github.raw"
        response = await client.get(url, headers=headers, params={"ref": commit_sha})
        self._handle_response_error(
            response, f"get_file_content({owner}/{name}, {commit_sha}, {path})"
        )
        return response.content

    async def list_branches(self, owner: str, name: str) -> list[str]:
        client = self._get_client()
        url = f"/repos/{owner}/{name}/branches"
        response = await client.get(url, headers=self._get_headers())
        self._handle_response_error(response, f"list_branches({owner}/{name})")

        data: list[dict[str, Any]] = response.json()
        return [b["name"] for b in data if "name" in b]

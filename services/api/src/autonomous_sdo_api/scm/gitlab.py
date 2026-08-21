from datetime import datetime
from typing import Any
from urllib.parse import quote

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


class GitLabAdapter(ScmProviderAdapter):
    """GitLab REST API v4 implementation of ScmProviderAdapter."""

    def __init__(
        self,
        token: str | None = None,
        api_base_url: str = "https://gitlab.com/api/v4",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._token = token
        self._api_base_url = api_base_url.rstrip("/")
        self._client = client
        self._owns_client = client is None

    @property
    def provider(self) -> ScmProvider:
        return ScmProvider.GITLAB

    def _get_headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "ASDO-Autonomous-SDO/1.0",
        }
        if self._token:
            headers["PRIVATE-TOKEN"] = self._token
        return headers

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
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
            raise ScmAuthenticationError(
                f"GitLab auth failed ({status}) during {action_desc}: {response.text}",
                provider=ScmProvider.GITLAB,
            )
        if status == 429:
            raise ScmRateLimitError(
                f"GitLab rate limit exceeded during {action_desc}",
                provider=ScmProvider.GITLAB,
            )
        if status == 404:
            raise ScmNotFoundError(
                f"GitLab resource not found during {action_desc}",
                provider=ScmProvider.GITLAB,
            )
        raise ScmError(
            f"GitLab API error ({status}) during {action_desc}: {response.text}",
            provider=ScmProvider.GITLAB,
        )

    def _encoded_project_path(self, owner: str, name: str) -> str:
        return quote(f"{owner}/{name}", safe="")

    async def get_repository(self, owner: str, name: str) -> RepositoryDescriptor:
        client = self._get_client()
        project_path = self._encoded_project_path(owner, name)
        url = f"{self._api_base_url}/projects/{project_path}"
        response = await client.get(url, headers=self._get_headers())
        self._handle_response_error(response, f"get_repository({owner}/{name})")

        data = response.json()
        visibility_str = data.get("visibility", "private")
        visibility = RepositoryVisibility.PRIVATE
        if visibility_str == "public":
            visibility = RepositoryVisibility.PUBLIC
        elif visibility_str == "internal":
            visibility = RepositoryVisibility.INTERNAL

        return RepositoryDescriptor(
            provider=ScmProvider.GITLAB,
            id=str(data["id"]),
            owner=data.get("namespace", {}).get("full_path", owner),
            name=data["name"],
            full_name=data.get("path_with_namespace", f"{owner}/{name}"),
            default_branch=data.get("default_branch", "main"),
            visibility=visibility,
            clone_url_http=data["http_url_to_repo"],
            clone_url_ssh=data["ssh_url_to_repo"],
            is_archived=bool(data.get("archived", False)),
        )

    async def resolve_commit(self, owner: str, name: str, ref: str) -> CommitResolution:
        client = self._get_client()
        project_path = self._encoded_project_path(owner, name)
        url = (
            f"{self._api_base_url}/projects/{project_path}/repository/commits/{quote(ref, safe='')}"
        )
        response = await client.get(url, headers=self._get_headers())
        self._handle_response_error(response, f"resolve_commit({owner}/{name}, {ref})")

        data = response.json()
        commit_sha = data["id"]
        date_str = data.get("authored_date") or data.get("created_at")
        authored_at = datetime.fromisoformat(date_str) if date_str else datetime.now()
        parent_ids = data.get("parent_ids", [])

        return CommitResolution(
            provider=ScmProvider.GITLAB,
            repository_id=f"{owner}/{name}",
            commit_sha=commit_sha,
            ref_requested=ref,
            message=data.get("message", ""),
            author_name=data.get("author_name", "unknown"),
            author_email=data.get("author_email", "unknown"),
            authored_at=authored_at,
            parent_shas=parent_ids,
        )

    async def get_file_content(self, owner: str, name: str, commit_sha: str, path: str) -> bytes:
        client = self._get_client()
        project_path = self._encoded_project_path(owner, name)
        encoded_path = quote(path.lstrip("/"), safe="")
        url = f"{self._api_base_url}/projects/{project_path}/repository/files/{encoded_path}/raw"
        response = await client.get(url, headers=self._get_headers(), params={"ref": commit_sha})
        self._handle_response_error(
            response, f"get_file_content({owner}/{name}, {commit_sha}, {path})"
        )
        return response.content

    async def list_branches(self, owner: str, name: str) -> list[str]:
        client = self._get_client()
        project_path = self._encoded_project_path(owner, name)
        url = f"{self._api_base_url}/projects/{project_path}/repository/branches"
        response = await client.get(url, headers=self._get_headers())
        self._handle_response_error(response, f"list_branches({owner}/{name})")

        data: list[dict[str, Any]] = response.json()
        return [b["name"] for b in data if "name" in b]

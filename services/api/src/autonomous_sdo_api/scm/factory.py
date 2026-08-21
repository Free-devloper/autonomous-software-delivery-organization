from autonomous_sdo_api.scm.adapter import ScmProviderAdapter
from autonomous_sdo_api.scm.github import GitHubAdapter
from autonomous_sdo_api.scm.gitlab import GitLabAdapter
from autonomous_sdo_api.scm.models import ScmError, ScmProvider


def get_scm_adapter(
    provider: ScmProvider | str,
    token: str | None = None,
    api_base_url: str | None = None,
) -> ScmProviderAdapter:
    """Factory to instantiate the appropriate provider adapter."""
    provider_str = str(provider).lower()
    if provider_str == ScmProvider.GITHUB:
        if api_base_url is not None:
            return GitHubAdapter(token=token, api_base_url=api_base_url)
        return GitHubAdapter(token=token)

    if provider_str == ScmProvider.GITLAB:
        if api_base_url is not None:
            return GitLabAdapter(token=token, api_base_url=api_base_url)
        return GitLabAdapter(token=token)

    raise ScmError(f"Unsupported SCM provider: '{provider}'", provider=provider_str)

from autonomous_sdo_api.sandbox.models import NetworkPolicy


class SandboxNetworkGuard:
    """Network egress isolation and policy enforcement for sandboxed executions."""

    @staticmethod
    def get_network_isolation_env(
        policy: NetworkPolicy,
        internal_hosts: list[str] | None = None,
    ) -> dict[str, str]:
        """Generate network containment environment variables based on the active policy."""
        if policy == NetworkPolicy.DENY_ALL:
            return {
                "NO_PROXY": "*",
                "HTTP_PROXY": "http://127.0.0.1:0",
                "HTTPS_PROXY": "http://127.0.0.1:0",
                "ALL_PROXY": "socks5://127.0.0.1:0",
                "ASDO_NETWORK_ISOLATION": "deny_all",
            }

        allowed = internal_hosts or ["localhost", "127.0.0.1", "metadata.internal"]
        return {
            "NO_PROXY": ",".join(allowed),
            "ASDO_NETWORK_ISOLATION": "allow_internal_only",
        }

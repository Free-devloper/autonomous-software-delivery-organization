from abc import ABC, abstractmethod

from autonomous_sdo_api.sandbox.models import ExecutionCommand, ExecutionResult, SandboxDescriptor


class SandboxRuntimeAdapter(ABC):
    """Abstract interface for hardened sandbox runtime adapters."""

    @abstractmethod
    async def provision(self, descriptor: SandboxDescriptor) -> None:
        """Provision the isolated sandbox environment."""

    @abstractmethod
    async def execute(
        self, descriptor: SandboxDescriptor, command: ExecutionCommand
    ) -> ExecutionResult:
        """Execute a command within the isolated sandbox with resource and timeout bounds."""

    @abstractmethod
    async def terminate(self, descriptor: SandboxDescriptor) -> None:
        """Terminate sandbox processes and tear down isolated storage/namespaces."""

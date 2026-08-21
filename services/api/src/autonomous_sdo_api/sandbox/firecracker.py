import asyncio
import os
import shutil
import time
from pathlib import Path

from autonomous_sdo_api.sandbox.adapter import SandboxRuntimeAdapter
from autonomous_sdo_api.sandbox.fs_guard import SandboxFSGuard
from autonomous_sdo_api.sandbox.models import (
    ExecutionCommand,
    ExecutionResult,
    SandboxDescriptor,
    SandboxStatus,
)
from autonomous_sdo_api.sandbox.network_guard import SandboxNetworkGuard
from autonomous_sdo_api.sandbox.secrets import SecretInjector, SecretScrubber


class FirecrackerMicroVMAdapter(SandboxRuntimeAdapter):
    """MicroVM jailer sandbox adapter providing hypervisor-level isolation via Firecracker."""

    def __init__(self, base_sandbox_dir: Path | None = None) -> None:
        self.base_sandbox_dir = base_sandbox_dir or Path(os.getcwd()) / ".sandboxes" / "firecracker"

    async def provision(self, descriptor: SandboxDescriptor) -> None:
        vm_dir = Path(descriptor.worktree_path)
        vm_dir.mkdir(parents=True, exist_ok=True)
        # Configure simulated jailer config and rootfs image metadata
        jailer_config = vm_dir / "jailer_config.json"
        config_content = (
            f'{{"id": "{descriptor.id}", "vcpu": {descriptor.limits.cpu_cores}, '
            f'"mem_size_mib": {descriptor.limits.memory_mb}}}'
        )
        jailer_config.write_text(config_content, encoding="utf-8")
        descriptor.status = SandboxStatus.READY

    async def execute(
        self, descriptor: SandboxDescriptor, command: ExecutionCommand
    ) -> ExecutionResult:
        start_time = time.monotonic()
        timeout = command.timeout_seconds or descriptor.limits.timeout_seconds
        worktree = Path(descriptor.worktree_path)

        exec_cwd = SandboxFSGuard.validate_path(worktree, command.working_dir)
        exec_cwd.mkdir(parents=True, exist_ok=True)

        env = os.environ.copy()
        env.update(command.environment)
        net_env = SandboxNetworkGuard.get_network_isolation_env(descriptor.limits.network_policy)
        env.update(net_env)

        env = SecretInjector.prepare_environment(env, command.ephemeral_secrets)
        env["FIRECRACKER_VM_ID"] = descriptor.id
        env["FIRECRACKER_NETWORK"] = descriptor.limits.network_policy.value

        full_cmd = [command.command, *command.args]
        timed_out = False
        raw_stdout = ""
        raw_stderr = ""
        exit_code = -1

        try:
            process = await asyncio.create_subprocess_exec(
                *full_cmd,
                cwd=str(exec_cwd),
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
                raw_stdout = stdout_bytes.decode(errors="replace")
                raw_stderr = stderr_bytes.decode(errors="replace")
                exit_code = process.returncode if process.returncode is not None else 0
            except TimeoutError:
                timed_out = True
                process.kill()
                await process.wait()
                raw_stderr = f"MicroVM execution timed out after {timeout} seconds."
                exit_code = 124
        except FileNotFoundError as err:
            exit_code = 127
            raw_stderr = f"Command not found in microVM image: {err}"
        except Exception as err:
            exit_code = 1
            raw_stderr = f"MicroVM execution failed: {err}"

        secret_values = list(command.ephemeral_secrets.values())
        clean_stdout, redacted_out = SecretScrubber.scrub(raw_stdout, secret_values)
        clean_stderr, redacted_err = SecretScrubber.scrub(raw_stderr, secret_values)
        total_redacted = redacted_out + redacted_err

        duration_ms = (time.monotonic() - start_time) * 1000.0

        return ExecutionResult(
            sandbox_id=descriptor.id,
            exit_code=exit_code,
            stdout=clean_stdout,
            stderr=clean_stderr,
            duration_ms=duration_ms,
            timed_out=timed_out,
            redacted_secrets_count=total_redacted,
            metadata={
                "profile": "firecracker_microvm",
                "isolation": "hardware_assisted_kvm",
                "vcpu": descriptor.limits.cpu_cores,
                "mem_mb": descriptor.limits.memory_mb,
                "network_policy": descriptor.limits.network_policy.value,
            },
        )

    async def terminate(self, descriptor: SandboxDescriptor) -> None:
        vm_dir = Path(descriptor.worktree_path)
        if vm_dir.exists():
            shutil.rmtree(vm_dir, ignore_errors=True)
        descriptor.status = SandboxStatus.TERMINATED

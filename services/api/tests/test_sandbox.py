from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from autonomous_sdo_api.app import create_app
from autonomous_sdo_api.config import Settings
from autonomous_sdo_api.database.tenancy import OrganizationContext, get_organization_context
from autonomous_sdo_api.policy import Role
from autonomous_sdo_api.sandbox.controller import SandboxController
from autonomous_sdo_api.sandbox.firecracker import FirecrackerMicroVMAdapter
from autonomous_sdo_api.sandbox.models import (
    CreateSandboxRequest,
    ExecutionCommand,
    NetworkPolicy,
    SandboxDescriptor,
    SandboxLimits,
    SandboxProfile,
    SandboxStatus,
)
from autonomous_sdo_api.sandbox.rootless import RootlessContainerAdapter
from autonomous_sdo_api.sandbox.routes import get_sandbox_controller

pytestmark = pytest.mark.unit


@pytest.mark.anyio
async def test_rootless_container_lifecycle() -> None:
    with TemporaryDirectory() as tmpdir:
        adapter = RootlessContainerAdapter(base_sandbox_dir=Path(tmpdir))
        descriptor = SandboxDescriptor(
            organization_id=uuid4(),
            requirement_id="req-1",
            plan_id="plan-1",
            work_package_id="pkg-1",
            profile=SandboxProfile.ROOTLESS_CONTAINER,
            limits=SandboxLimits(timeout_seconds=5, network_policy=NetworkPolicy.DENY_ALL),
            worktree_path=str(Path(tmpdir) / "worktree-1"),
        )

        await adapter.provision(descriptor)
        assert descriptor.status == SandboxStatus.READY
        assert Path(descriptor.worktree_path).exists()

        # Execute simple command (echo)
        cmd = ExecutionCommand(command="python", args=["-c", "print('hello-sandbox')"])
        res = await adapter.execute(descriptor, cmd)
        assert res.exit_code == 0
        assert "hello-sandbox" in res.stdout
        assert not res.timed_out
        assert res.metadata["profile"] == "rootless_container"

        # Execute command timeout test
        cmd_timeout = ExecutionCommand(
            command="python",
            args=["-c", "import time; time.sleep(2)"],
            timeout_seconds=1,
        )
        res_timeout = await adapter.execute(descriptor, cmd_timeout)
        assert res_timeout.timed_out
        assert res_timeout.exit_code == 124

        # Execute command not found test
        cmd_invalid = ExecutionCommand(command="non_existent_binary_xyz123")
        res_invalid = await adapter.execute(descriptor, cmd_invalid)
        assert res_invalid.exit_code == 127

        await adapter.terminate(descriptor)
        assert descriptor.status.value == SandboxStatus.TERMINATED.value


@pytest.mark.anyio
async def test_firecracker_microvm_lifecycle() -> None:
    with TemporaryDirectory() as tmpdir:
        adapter = FirecrackerMicroVMAdapter(base_sandbox_dir=Path(tmpdir))
        descriptor = SandboxDescriptor(
            organization_id=uuid4(),
            requirement_id="req-2",
            plan_id="plan-2",
            work_package_id="pkg-2",
            profile=SandboxProfile.FIRECRACKER_MICROVM,
            limits=SandboxLimits(cpu_cores=4, memory_mb=4096),
            worktree_path=str(Path(tmpdir) / "vm-2"),
        )

        await adapter.provision(descriptor)
        assert descriptor.status.value == SandboxStatus.READY.value
        assert (Path(descriptor.worktree_path) / "jailer_config.json").exists()

        cmd = ExecutionCommand(command="python", args=["-c", "print('hello-microvm')"])
        res = await adapter.execute(descriptor, cmd)
        assert res.exit_code == 0
        assert "hello-microvm" in res.stdout
        assert res.metadata["profile"] == "firecracker_microvm"
        assert res.metadata["vcpu"] == 4

        # Timeout test
        cmd_timeout = ExecutionCommand(
            command="python",
            args=["-c", "import time; time.sleep(2)"],
            timeout_seconds=1,
        )
        res_timeout = await adapter.execute(descriptor, cmd_timeout)
        assert res_timeout.timed_out
        assert res_timeout.exit_code == 124

        await adapter.terminate(descriptor)
        assert descriptor.status.value == SandboxStatus.TERMINATED.value


@pytest.mark.anyio
async def test_sandbox_controller_tenant_isolation() -> None:
    with TemporaryDirectory() as tmpdir:
        controller = SandboxController(base_work_dir=Path(tmpdir))
        org_a = uuid4()
        org_b = uuid4()

        req = CreateSandboxRequest(
            requirement_id="req-iso",
            plan_id="plan-iso",
            work_package_id="pkg-iso",
            profile=SandboxProfile.ROOTLESS_CONTAINER,
        )

        sbx_a = await controller.create_sandbox(org_a, req)
        assert sbx_a.organization_id == org_a

        # Org A can get and list sandbox
        assert controller.get_sandbox(org_a, sbx_a.id).id == sbx_a.id
        assert len(controller.list_sandboxes(org_a)) == 1

        # Org B cannot access Org A sandbox (Tenant Isolation)
        assert len(controller.list_sandboxes(org_b)) == 0
        with pytest.raises(KeyError):
            controller.get_sandbox(org_b, sbx_a.id)

        # Execute command in Org A
        cmd = ExecutionCommand(command="python", args=["-c", "print('tenant-a-execution')"])
        res = await controller.execute_command(org_a, sbx_a.id, cmd)
        assert res.exit_code == 0
        assert "tenant-a-execution" in res.stdout

        # Terminate
        await controller.terminate_sandbox(org_a, sbx_a.id)
        assert len(controller.list_sandboxes(org_a)) == 0


def test_sandbox_api_routes() -> None:
    settings = Settings(service_name="asdo-sandbox-api-test")
    app = create_app(settings=settings)
    client = TestClient(app)

    org_id = UUID("018f0000-0000-7000-8000-000000000001")
    other_org = UUID("018f0000-0000-7000-8000-000000000002")

    controller = SandboxController()
    app.dependency_overrides[get_sandbox_controller] = lambda: controller
    app.dependency_overrides[get_organization_context] = lambda: OrganizationContext(
        organization_id=org_id,
        actor_id="usr-test-1",
        roles=frozenset({Role.REPOSITORY_MAINTAINER}),
    )

    # 1. Create sandbox
    create_payload = {
        "requirement_id": "req-api-1",
        "plan_id": "plan-api-1",
        "work_package_id": "pkg-api-1",
        "profile": "rootless_container",
        "limits": {
            "cpu_cores": 2,
            "memory_mb": 2048,
            "disk_mb": 8192,
            "timeout_seconds": 60,
            "network_policy": "deny_all",
        },
    }
    resp = client.post("/api/v1/sandboxes", json=create_payload)
    assert resp.status_code == 201
    sbx_data = resp.json()
    sbx_id = sbx_data["id"]
    assert sbx_data["status"] == "ready"

    # 2. List sandboxes
    list_resp = client.get("/api/v1/sandboxes")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    # 3. Get sandbox
    get_resp = client.get(f"/api/v1/sandboxes/{sbx_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == sbx_id

    # 4. Execute command
    exec_payload = {
        "command": "python",
        "args": ["-c", "print('api-execution-success')"],
    }
    exec_resp = client.post(f"/api/v1/sandboxes/{sbx_id}/execute", json=exec_payload)
    assert exec_resp.status_code == 200
    assert "api-execution-success" in exec_resp.json()["stdout"]

    # 5. Cross-tenant access denied
    app.dependency_overrides[get_organization_context] = lambda: OrganizationContext(
        organization_id=other_org,
        actor_id="usr-other-tenant",
        roles=frozenset({Role.REPOSITORY_MAINTAINER}),
    )
    cross_resp = client.get(f"/api/v1/sandboxes/{sbx_id}")
    assert cross_resp.status_code == 404

    # 6. Switch back and terminate
    app.dependency_overrides[get_organization_context] = lambda: OrganizationContext(
        organization_id=org_id,
        actor_id="usr-test-1",
        roles=frozenset({Role.REPOSITORY_MAINTAINER}),
    )
    del_resp = client.delete(f"/api/v1/sandboxes/{sbx_id}")
    assert del_resp.status_code == 204

    # Verify deleted
    get_del_resp = client.get(f"/api/v1/sandboxes/{sbx_id}")
    assert get_del_resp.status_code == 404

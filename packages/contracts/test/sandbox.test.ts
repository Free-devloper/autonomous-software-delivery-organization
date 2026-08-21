import { describe, expect, it } from "vitest";

import {
  createSandboxRequestSchema,
  executeCommandRequestSchema,
  networkPolicySchema,
  sandboxDescriptorSchema,
  sandboxExecutionResultSchema,
  sandboxLimitsSchema,
  sandboxProfileSchema,
} from "../src/index";

describe("Sandbox contracts", () => {
  const timestamp = "2026-08-20T12:00:00.000Z";

  it("validates sandbox profiles and network policies", () => {
    expect(sandboxProfileSchema.parse("rootless_container")).toBe("rootless_container");
    expect(sandboxProfileSchema.parse("firecracker_microvm")).toBe("firecracker_microvm");
    expect(networkPolicySchema.parse("deny_all")).toBe("deny_all");
    expect(networkPolicySchema.parse("allow_internal_only")).toBe("allow_internal_only");

    expect(() => sandboxProfileSchema.parse("privileged_docker")).toThrow();
    expect(() => networkPolicySchema.parse("allow_all")).toThrow();
  });

  it("validates sandbox resource limits with sensible defaults", () => {
    const defaultLimits = sandboxLimitsSchema.parse({});
    expect(defaultLimits.cpu_cores).toBe(2);
    expect(defaultLimits.memory_mb).toBe(2048);
    expect(defaultLimits.disk_mb).toBe(8192);
    expect(defaultLimits.timeout_seconds).toBe(300);
    expect(defaultLimits.network_policy).toBe("deny_all");

    const customLimits = {
      cpu_cores: 4,
      memory_mb: 4096,
      disk_mb: 16384,
      timeout_seconds: 600,
      network_policy: "allow_internal_only" as const,
    };
    expect(sandboxLimitsSchema.parse(customLimits)).toEqual(customLimits);
  });

  it("validates sandbox creation and execution request payloads", () => {
    const createReq = {
      requirement_id: "req-101",
      plan_id: "plan-101",
      work_package_id: "pkg-1",
      profile: "rootless_container" as const,
      limits: {
        cpu_cores: 2,
        memory_mb: 2048,
        disk_mb: 8192,
        timeout_seconds: 300,
        network_policy: "deny_all" as const,
      },
    };
    expect(createSandboxRequestSchema.parse(createReq)).toEqual(createReq);

    const execReq = {
      command: "pytest",
      args: ["-v", "--maxfail=1"],
      working_dir: "/workspace/project",
      environment: { CI: "true" },
      ephemeral_secrets: { GITHUB_TOKEN: "ghp_12345" },
      timeout_seconds: 60,
    };
    expect(executeCommandRequestSchema.parse(execReq)).toEqual(execReq);
  });

  it("validates sandbox descriptor and execution result", () => {
    const descriptor = {
      id: "sbx-001",
      requirement_id: "req-101",
      plan_id: "plan-101",
      work_package_id: "pkg-1",
      profile: "firecracker_microvm" as const,
      limits: {
        cpu_cores: 4,
        memory_mb: 4096,
        disk_mb: 16384,
        timeout_seconds: 600,
        network_policy: "deny_all" as const,
      },
      status: "ready" as const,
      worktree_path: "/var/sandboxes/sbx-001",
      created_at: timestamp,
    };
    expect(sandboxDescriptorSchema.parse(descriptor)).toEqual(descriptor);

    const result = {
      sandbox_id: "sbx-001",
      exit_code: 0,
      stdout: "5 passed in 0.45s\n",
      stderr: "",
      duration_ms: 450,
      timed_out: false,
      redacted_secrets_count: 1,
    };
    expect(sandboxExecutionResultSchema.parse(result)).toEqual(result);
  });
});

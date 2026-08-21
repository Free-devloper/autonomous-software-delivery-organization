import { z } from "zod";

/** Supported sandbox runtime isolation profiles. */
export const sandboxProfileSchema = z.enum(["rootless_container", "firecracker_microvm"]);
export type SandboxProfile = z.infer<typeof sandboxProfileSchema>;

/** Network egress policy applied to sandboxed executions. */
export const networkPolicySchema = z.enum(["deny_all", "allow_internal_only"]);
export type NetworkPolicy = z.infer<typeof networkPolicySchema>;

/** Resource limits enforced inside sandbox environments. */
export const sandboxLimitsSchema = z
  .object({
    cpu_cores: z.number().positive().max(16).default(2),
    memory_mb: z.number().int().positive().max(32768).default(2048),
    disk_mb: z.number().int().positive().max(65536).default(8192),
    timeout_seconds: z.number().int().positive().max(3600).default(300),
    network_policy: networkPolicySchema.default("deny_all"),
  })
  .strict();
export type SandboxLimits = z.infer<typeof sandboxLimitsSchema>;

/** Request payload to provision an isolated execution sandbox. */
export const createSandboxRequestSchema = z
  .object({
    requirement_id: z.string().min(1),
    plan_id: z.string().min(1),
    work_package_id: z.string().min(1),
    profile: sandboxProfileSchema.default("rootless_container"),
    limits: sandboxLimitsSchema.optional(),
  })
  .strict();
export type CreateSandboxRequest = z.infer<typeof createSandboxRequestSchema>;

/** Active sandbox instance descriptor. */
export const sandboxDescriptorSchema = z
  .object({
    id: z.string().min(1),
    requirement_id: z.string().min(1),
    plan_id: z.string().min(1),
    work_package_id: z.string().min(1),
    profile: sandboxProfileSchema,
    limits: sandboxLimitsSchema,
    status: z.enum(["provisioning", "ready", "executing", "terminated", "failed"]),
    worktree_path: z.string().min(1),
    created_at: z.iso.datetime(),
  })
  .strict();
export type SandboxDescriptor = z.infer<typeof sandboxDescriptorSchema>;

/** Request payload to execute a command within a running sandbox. */
export const executeCommandRequestSchema = z
  .object({
    command: z.string().min(1),
    args: z.array(z.string()).default([]),
    working_dir: z.string().optional(),
    environment: z.record(z.string(), z.string()).default({}),
    ephemeral_secrets: z.record(z.string(), z.string()).default({}),
    timeout_seconds: z.number().int().positive().max(3600).optional(),
  })
  .strict();
export type ExecuteCommandRequest = z.infer<typeof executeCommandRequestSchema>;

/** Result of a command execution within a sandbox. */
export const sandboxExecutionResultSchema = z
  .object({
    sandbox_id: z.string().min(1),
    exit_code: z.number().int(),
    stdout: z.string(),
    stderr: z.string(),
    duration_ms: z.number().nonnegative(),
    timed_out: z.boolean().default(false),
    redacted_secrets_count: z.number().int().nonnegative().default(0),
  })
  .strict();
export type SandboxExecutionResult = z.infer<typeof sandboxExecutionResultSchema>;

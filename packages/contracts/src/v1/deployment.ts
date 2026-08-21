/**
 * Type definitions and contracts for Phase 6: Deployment & Rollback.
 */

import { z } from "zod";

export const ReleaseStrategySchema = z.enum(["rolling", "canary", "blue_green"]);
export type ReleaseStrategy = z.infer<typeof ReleaseStrategySchema>;

export const DeploymentEnvironmentSchema = z.enum(["development", "staging", "production"]);
export type DeploymentEnvironment = z.infer<typeof DeploymentEnvironmentSchema>;

export const DeploymentStatusSchema = z.enum([
  "draft",
  "pending_approval",
  "approved",
  "in_progress",
  "canary_validating",
  "promoted",
  "completed",
  "failed",
  "rollback_pending_approval",
  "rollback_approved",
  "rolling_back",
  "rolled_back",
]);
export type DeploymentStatus = z.infer<typeof DeploymentStatusSchema>;

export const MigrationRiskLevelSchema = z.enum(["none", "low", "medium", "high", "breaking"]);
export type MigrationRiskLevel = z.infer<typeof MigrationRiskLevelSchema>;

export const SchemaMigrationPlanSchema = z.object({
  id: z.string(),
  migration_name: z.string(),
  version: z.string(),
  is_backward_compatible: z.boolean(),
  expand_contract_step: z.enum(["expand", "migrate", "contract", "standalone"]),
  estimated_duration_seconds: z.number().nonnegative(),
  risk_level: MigrationRiskLevelSchema,
  rollback_sql: z.string().optional(),
});
export type SchemaMigrationPlan = z.infer<typeof SchemaMigrationPlanSchema>;

export const DeploymentApprovalPurposeSchema = z.enum(["deploy", "rollback"]);
export type DeploymentApprovalPurpose = z.infer<typeof DeploymentApprovalPurposeSchema>;

export const DeploymentApprovalSchema = z.object({
  id: z.string(),
  plan_id: z.string(),
  approver_id: z.string(),
  purpose: DeploymentApprovalPurposeSchema,
  artifact_digest: z.string().regex(/^[a-f0-9]{64}$/, "Must be a 64-character SHA-256 digest"),
  environment: DeploymentEnvironmentSchema,
  approved_at: z.iso.datetime(),
  expires_at: z.iso.datetime(),
  notes: z.string().default(""),
});
export type DeploymentApproval = z.infer<typeof DeploymentApprovalSchema>;

export const SloGateMetricSchema = z.object({
  metric_name: z.string(),
  target_value: z.number(),
  actual_value: z.number(),
  passed: z.boolean(),
  unit: z.string(),
});
export type SloGateMetric = z.infer<typeof SloGateMetricSchema>;

export const ReleasePlanSchema = z.object({
  id: z.string(),
  organization_id: z.uuid(),
  title: z.string().min(1),
  version: z.string(),
  artifact_digest: z.string().regex(/^[a-f0-9]{64}$/, "Must be a 64-character SHA-256 digest"),
  artifact_image: z.string(),
  strategy: ReleaseStrategySchema,
  target_environment: DeploymentEnvironmentSchema,
  status: DeploymentStatusSchema,
  migrations: z.array(SchemaMigrationPlanSchema).default([]),
  canary_weight_percentage: z.number().min(0).max(100).default(10),
  canary_duration_seconds: z.number().nonnegative().default(300),
  slo_gates: z.array(SloGateMetricSchema).default([]),
  deploy_approvals: z.array(DeploymentApprovalSchema).default([]),
  rollback_approvals: z.array(DeploymentApprovalSchema).default([]),
  created_by: z.string(),
  created_at: z.iso.datetime(),
  updated_at: z.iso.datetime().optional(),
  completed_at: z.iso.datetime().optional(),
});
export type ReleasePlan = z.infer<typeof ReleasePlanSchema>;

export const RollbackRequestSchema = z.object({
  plan_id: z.string(),
  target_digest: z.string().regex(/^[a-f0-9]{64}$/, "Must be a 64-character SHA-256 digest"),
  reason: z.string().min(1),
  requested_by: z.string(),
  force_without_migration_rollback: z.boolean().default(false),
});
export type RollbackRequest = z.infer<typeof RollbackRequestSchema>;

export const PostRollbackCheckResultSchema = z.object({
  check_name: z.string(),
  passed: z.boolean(),
  details: z.string(),
  checked_at: z.iso.datetime(),
});
export type PostRollbackCheckResult = z.infer<typeof PostRollbackCheckResultSchema>;

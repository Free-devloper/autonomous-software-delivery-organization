import { describe, expect, it } from "vitest";

import {
  DeploymentApprovalPurposeSchema,
  DeploymentApprovalSchema,
  DeploymentEnvironmentSchema,
  DeploymentStatusSchema,
  MigrationRiskLevelSchema,
  PostRollbackCheckResultSchema,
  ReleasePlanSchema,
  ReleaseStrategySchema,
  RollbackRequestSchema,
  SchemaMigrationPlanSchema,
  SloGateMetricSchema,
} from "../src/v1/deployment";

describe("Deployment Contracts", () => {
  const dummyDigest = "a".repeat(64);

  it("validates release strategies", () => {
    expect(ReleaseStrategySchema.parse("rolling")).toBe("rolling");
    expect(ReleaseStrategySchema.parse("canary")).toBe("canary");
    expect(ReleaseStrategySchema.parse("blue_green")).toBe("blue_green");
    expect(() => ReleaseStrategySchema.parse("invalid")).toThrow();
  });

  it("validates deployment environments and statuses", () => {
    expect(DeploymentEnvironmentSchema.parse("production")).toBe("production");
    expect(DeploymentStatusSchema.parse("canary_validating")).toBe("canary_validating");
    expect(DeploymentStatusSchema.parse("rolled_back")).toBe("rolled_back");
    expect(MigrationRiskLevelSchema.parse("breaking")).toBe("breaking");
  });

  it("validates schema migration plans and slo gate metrics", () => {
    const slo = SloGateMetricSchema.parse({
      metric_name: "p99_latency_ms",
      target_value: 200,
      actual_value: 150,
      passed: true,
      unit: "ms",
    });
    expect(slo.passed).toBe(true);

    const plan = SchemaMigrationPlanSchema.parse({
      id: "mig-001",
      migration_name: "add_tenant_indexes",
      version: "20260820_01",
      is_backward_compatible: true,
      expand_contract_step: "expand",
      estimated_duration_seconds: 45,
      risk_level: "low",
      rollback_sql: "DROP INDEX CONCURRENTLY idx_tenants;",
    });
    expect(plan.id).toBe("mig-001");
    expect(plan.is_backward_compatible).toBe(true);
  });

  it("validates purpose-bound deployment and rollback approvals", () => {
    expect(DeploymentApprovalPurposeSchema.parse("deploy")).toBe("deploy");
    expect(DeploymentApprovalPurposeSchema.parse("rollback")).toBe("rollback");

    const approval = DeploymentApprovalSchema.parse({
      id: "appr-001",
      plan_id: "rel-001",
      approver_id: "user-rel-mgr-1",
      purpose: "deploy",
      artifact_digest: dummyDigest,
      environment: "production",
      approved_at: "2026-08-20T10:00:00Z",
      expires_at: "2026-08-20T18:00:00Z",
      notes: "Release approved by release manager",
    });
    expect(approval.purpose).toBe("deploy");
  });

  it("validates full release plan with canary, slo gates and approvals", () => {
    const plan = ReleasePlanSchema.parse({
      id: "rel-001",
      organization_id: "a1b2c3d4-e5f6-4a1b-8c2d-3e4f5a6b7c8d",
      title: "v1.2.0 Production Release",
      version: "1.2.0",
      artifact_digest: dummyDigest,
      artifact_image: "ghcr.io/roytechworkforce/asdo:1.2.0",
      strategy: "canary",
      target_environment: "production",
      status: "canary_validating",
      canary_weight_percentage: 20,
      canary_duration_seconds: 600,
      slo_gates: [
        {
          metric_name: "p99_latency_ms",
          target_value: 200,
          actual_value: 145,
          passed: true,
          unit: "ms",
        },
      ],
      created_by: "user-1",
      created_at: "2026-08-20T09:00:00Z",
    });
    expect(plan.status).toBe("canary_validating");
    expect(plan.slo_gates[0]?.passed).toBe(true);
  });

  it("validates rollback requests and post-rollback verification checks", () => {
    const req = RollbackRequestSchema.parse({
      plan_id: "rel-001",
      target_digest: dummyDigest,
      reason: "Latency degradation on canary traffic",
      requested_by: "user-oncall-1",
    });
    expect(req.force_without_migration_rollback).toBe(false);

    const check = PostRollbackCheckResultSchema.parse({
      check_name: "database_schema_compatibility",
      passed: true,
      details: "Schema intact with zero corrupted rows",
      checked_at: "2026-08-20T09:30:00Z",
    });
    expect(check.passed).toBe(true);
  });
});

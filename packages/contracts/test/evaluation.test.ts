import { describe, expect, it } from "vitest";

import {
  BackupJobSchema,
  BackupStatusSchema,
  BackupTypeSchema,
  CostReportSchema,
  EvaluationCategorySchema,
  EvaluationReportSchema,
  EvaluationStatusSchema,
  MetricScoreSchema,
  RestoreJobSchema,
} from "../src/v1/evaluation";

describe("Evaluation Contracts", () => {
  const dummyDigest = "b".repeat(64);

  it("validates evaluation categories and statuses", () => {
    expect(EvaluationCategorySchema.parse("security_recall")).toBe("security_recall");
    expect(EvaluationCategorySchema.parse("mutation_score")).toBe("mutation_score");
    expect(EvaluationStatusSchema.parse("passed")).toBe("passed");
    expect(EvaluationStatusSchema.parse("warning")).toBe("warning");
  });

  it("validates metric scores and evaluation reports", () => {
    const metric = MetricScoreSchema.parse({
      name: "mutation_score_overall",
      category: "mutation_score",
      score: 88.5,
      target_threshold: 80.0,
      passed: true,
      unit: "%",
      details: "Tested across 150 mutants",
    });
    expect(metric.passed).toBe(true);

    const report = EvaluationReportSchema.parse({
      id: "eval-001",
      organization_id: "a1b2c3d4-e5f6-4a1b-8c2d-3e4f5a6b7c8d",
      run_id: "run-999",
      overall_status: "passed",
      summary: "All production readiness thresholds satisfied",
      metrics: [metric],
      created_at: "2026-08-20T10:00:00Z",
    });
    expect(report.overall_status).toBe("passed");
    expect(report.evaluation_window_hours).toBe(24);
  });

  it("validates cost reports and token usage breakdown", () => {
    const cost = CostReportSchema.parse({
      id: "cost-001",
      organization_id: "a1b2c3d4-e5f6-4a1b-8c2d-3e4f5a6b7c8d",
      period_start: "2026-08-01T00:00:00Z",
      period_end: "2026-08-20T00:00:00Z",
      total_cost_usd: 142.5,
      budget_limit_usd: 500.0,
      budget_consumed_percentage: 28.5,
      is_within_budget: true,
      model_breakdown: [
        {
          model_name: "claude-3-5-sonnet",
          input_tokens: 1500000,
          output_tokens: 300000,
          total_tokens: 1800000,
          estimated_cost_usd: 120.0,
        },
      ],
    });
    expect(cost.is_within_budget).toBe(true);
    expect(cost.model_breakdown[0]?.total_tokens).toBe(1800000);
  });

  it("validates backup and restore jobs with RPO/RTO targets", () => {
    expect(BackupTypeSchema.parse("database")).toBe("database");
    expect(BackupStatusSchema.parse("completed")).toBe("completed");

    const backup = BackupJobSchema.parse({
      id: "bkp-001",
      organization_id: "a1b2c3d4-e5f6-4a1b-8c2d-3e4f5a6b7c8d",
      backup_type: "full",
      status: "completed",
      storage_uri: "s3://backups/asdo/20260820_full.tar.gz",
      artifact_digest: dummyDigest,
      size_bytes: 104857600,
      rpo_target_minutes: 15,
      rto_target_minutes: 60,
      created_at: "2026-08-20T02:00:00Z",
      completed_at: "2026-08-20T02:05:00Z",
    });
    expect(backup.rpo_target_minutes).toBe(15);

    const restore = RestoreJobSchema.parse({
      id: "rst-001",
      organization_id: "a1b2c3d4-e5f6-4a1b-8c2d-3e4f5a6b7c8d",
      backup_id: "bkp-001",
      status: "completed",
      observed_recovery_time_seconds: 180,
      data_integrity_verified: true,
      created_at: "2026-08-20T03:00:00Z",
      verified_at: "2026-08-20T03:03:00Z",
    });
    expect(restore.data_integrity_verified).toBe(true);
  });
});

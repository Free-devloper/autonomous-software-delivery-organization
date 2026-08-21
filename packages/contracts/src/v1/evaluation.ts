/**
 * Type definitions and contracts for Phase 7: Evaluation & Production Readiness.
 */

import { z } from "zod";

export const EvaluationCategorySchema = z.enum([
  "correctness",
  "security_recall",
  "performance_slo",
  "mutation_score",
  "flake_rate",
  "cost_efficiency",
  "recovery_readiness",
]);
export type EvaluationCategory = z.infer<typeof EvaluationCategorySchema>;

export const EvaluationStatusSchema = z.enum(["running", "passed", "warning", "failed"]);
export type EvaluationStatus = z.infer<typeof EvaluationStatusSchema>;

export const MetricScoreSchema = z.object({
  name: z.string(),
  category: EvaluationCategorySchema,
  score: z.number(),
  target_threshold: z.number(),
  passed: z.boolean(),
  unit: z.string(),
  details: z.string().default(""),
});
export type MetricScore = z.infer<typeof MetricScoreSchema>;

export const EvaluationReportSchema = z.object({
  id: z.string(),
  organization_id: z.uuid(),
  run_id: z.string(),
  overall_status: EvaluationStatusSchema,
  summary: z.string(),
  metrics: z.array(MetricScoreSchema),
  created_at: z.iso.datetime(),
  evaluation_window_hours: z.number().positive().default(24),
});
export type EvaluationReport = z.infer<typeof EvaluationReportSchema>;

export const TokenCostMetricSchema = z.object({
  model_name: z.string(),
  input_tokens: z.number().nonnegative(),
  output_tokens: z.number().nonnegative(),
  total_tokens: z.number().nonnegative(),
  estimated_cost_usd: z.number().nonnegative(),
});
export type TokenCostMetric = z.infer<typeof TokenCostMetricSchema>;

export const CostReportSchema = z.object({
  id: z.string(),
  organization_id: z.uuid(),
  period_start: z.iso.datetime(),
  period_end: z.iso.datetime(),
  total_cost_usd: z.number().nonnegative(),
  budget_limit_usd: z.number().positive(),
  budget_consumed_percentage: z.number().nonnegative(),
  is_within_budget: z.boolean(),
  model_breakdown: z.array(TokenCostMetricSchema),
});
export type CostReport = z.infer<typeof CostReportSchema>;

export const BackupTypeSchema = z.enum(["database", "vector_index", "audit_log", "full"]);
export type BackupType = z.infer<typeof BackupTypeSchema>;

export const BackupStatusSchema = z.enum(["pending", "in_progress", "completed", "failed"]);
export type BackupStatus = z.infer<typeof BackupStatusSchema>;

export const BackupJobSchema = z.object({
  id: z.string(),
  organization_id: z.uuid(),
  backup_type: BackupTypeSchema,
  status: BackupStatusSchema,
  storage_uri: z.string(),
  artifact_digest: z.string().regex(/^[a-f0-9]{64}$/, "Must be a 64-character SHA-256 digest"),
  size_bytes: z.number().nonnegative(),
  rpo_target_minutes: z.number().positive().default(15),
  rto_target_minutes: z.number().positive().default(60),
  created_at: z.iso.datetime(),
  completed_at: z.iso.datetime().optional(),
});
export type BackupJob = z.infer<typeof BackupJobSchema>;

export const RestoreJobSchema = z.object({
  id: z.string(),
  organization_id: z.uuid(),
  backup_id: z.string(),
  status: BackupStatusSchema,
  observed_recovery_time_seconds: z.number().nonnegative().optional(),
  data_integrity_verified: z.boolean().default(false),
  verified_at: z.iso.datetime().optional(),
  created_at: z.iso.datetime(),
});
export type RestoreJob = z.infer<typeof RestoreJobSchema>;

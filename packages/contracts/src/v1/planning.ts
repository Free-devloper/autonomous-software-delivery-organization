import { z } from "zod";

/** Specialized project agent roles for bounded work package dispatch. */
export const specialistRoleSchema = z.enum(["frontend", "backend", "testing", "reviewer"]);
export type SpecialistRole = z.infer<typeof specialistRoleSchema>;

/** Resource and financial budget constraints allocated to a work package or plan. */
export const workPackageBudgetSchema = z
  .object({
    max_tokens: z.number().int().positive().default(100000),
    max_duration_seconds: z.number().int().positive().default(600),
    max_cost_usd: z.number().min(0).default(5.0),
  })
  .strict();
export type WorkPackageBudget = z.infer<typeof workPackageBudgetSchema>;

/** Status of a work package during execution. */
export const workPackageStatusSchema = z.enum(["pending", "in_progress", "completed", "failed"]);
export type WorkPackageStatus = z.infer<typeof workPackageStatusSchema>;

/** An atomic, bounded unit of engineering work assigned to a specialist agent. */
export const workPackageSchema = z
  .object({
    id: z.string().min(1),
    requirement_id: z.string().min(1),
    revision_id: z.string().min(1),
    title: z.string().min(1),
    description: z.string().min(1),
    target_files: z.array(z.string()).min(1),
    acceptance_criteria_ids: z.array(z.string()).default([]),
    dependencies: z.array(z.string()).default([]),
    assigned_specialist: specialistRoleSchema,
    budget: workPackageBudgetSchema,
    status: workPackageStatusSchema.default("pending"),
    created_at: z.iso.datetime(),
  })
  .strict();
export type WorkPackage = z.infer<typeof workPackageSchema>;

/** Dependency edge in the execution DAG connecting two work packages. */
export const dagEdgeSchema = z
  .object({
    from_package_id: z.string().min(1),
    to_package_id: z.string().min(1),
  })
  .strict();
export type DagEdge = z.infer<typeof dagEdgeSchema>;

/** Architecture plan decomposing a requirement revision into a verified DAG of work packages. */
export const architecturePlanSchema = z
  .object({
    id: z.string().min(1),
    requirement_id: z.string().min(1),
    revision_id: z.string().min(1),
    summary: z.string().min(1),
    work_packages: z.array(workPackageSchema).min(1),
    edges: z.array(dagEdgeSchema).default([]),
    total_budget: workPackageBudgetSchema,
    is_approved: z.boolean().default(false),
    approval_rationale: z.string().optional(),
    approved_by: z.string().optional(),
    created_at: z.iso.datetime(),
  })
  .strict();
export type ArchitecturePlan = z.infer<typeof architecturePlanSchema>;

/** Request payload to generate an architecture plan. */
export const createPlanRequestSchema = z
  .object({
    requirement_id: z.string().min(1),
    revision_id: z.string().min(1),
    summary: z.string().min(1),
    work_packages: z.array(workPackageSchema).min(1),
    edges: z.array(dagEdgeSchema).default([]),
  })
  .strict();
export type CreatePlanRequest = z.infer<typeof createPlanRequestSchema>;

/** Request payload to approve an architecture plan. */
export const approvePlanRequestSchema = z
  .object({
    rationale: z.string().min(1),
  })
  .strict();
export type ApprovePlanRequest = z.infer<typeof approvePlanRequestSchema>;

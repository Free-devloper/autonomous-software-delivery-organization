import { z } from "zod";

/** Verification methods for individual acceptance criteria. */
export const verificationMethodSchema = z.enum([
  "automated_test",
  "manual_check",
  "contract_verification",
  "security_scan",
]);
export type VerificationMethod = z.infer<typeof verificationMethodSchema>;

/** Individual verifiable acceptance criterion. */
export const acceptanceCriterionSchema = z
  .object({
    id: z.string().min(1),
    criterion_text: z.string().min(1),
    verification_method: verificationMethodSchema,
    is_mandatory: z.boolean().default(true),
  })
  .strict();
export type AcceptanceCriterion = z.infer<typeof acceptanceCriterionSchema>;

/** Status of a requirement revision. */
export const requirementStatusSchema = z.enum([
  "draft",
  "pending_clarification",
  "approved",
  "in_progress",
  "completed",
  "superseded",
]);
export type RequirementStatus = z.infer<typeof requirementStatusSchema>;

/** An immutable revision of a requirement specification. */
export const requirementRevisionSchema = z
  .object({
    id: z.string().min(1),
    requirement_id: z.string().min(1),
    version: z.number().int().positive(),
    title: z.string().min(1),
    description: z.string().min(1),
    scope: z.string().default(""),
    acceptance_criteria: z.array(acceptanceCriterionSchema),
    status: requirementStatusSchema,
    author_id: z.string().min(1),
    created_at: z.iso.datetime(),
  })
  .strict();
export type RequirementRevision = z.infer<typeof requirementRevisionSchema>;

/** Clarification request status. */
export const clarificationStatusSchema = z.enum(["pending", "resolved"]);
export type ClarificationStatus = z.infer<typeof clarificationStatusSchema>;

/** Interactive clarification request for ambiguous or missing requirements. */
export const clarificationRequestSchema = z
  .object({
    id: z.string().min(1),
    requirement_id: z.string().min(1),
    question: z.string().min(1),
    options: z.array(z.string()).default([]),
    response: z.string().optional(),
    status: clarificationStatusSchema,
    created_at: z.iso.datetime(),
    resolved_at: z.iso.datetime().optional(),
  })
  .strict();
export type ClarificationRequest = z.infer<typeof clarificationRequestSchema>;

/** Request payload to create a new requirement or revision. */
export const createRequirementRequestSchema = z
  .object({
    title: z.string().min(1),
    description: z.string().min(1),
    scope: z.string().default(""),
    acceptance_criteria: z.array(acceptanceCriterionSchema).min(1),
  })
  .strict();
export type CreateRequirementRequest = z.infer<typeof createRequirementRequestSchema>;

/** Request payload to answer a clarification. */
export const resolveClarificationRequestSchema = z
  .object({
    response: z.string().min(1),
  })
  .strict();
export type ResolveClarificationRequest = z.infer<typeof resolveClarificationRequestSchema>;

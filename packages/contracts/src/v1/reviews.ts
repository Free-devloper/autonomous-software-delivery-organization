import { z } from "zod";

/** Status of a code review. */
export const reviewStatusSchema = z.enum([
  "pending",
  "in_progress",
  "approved",
  "changes_requested",
  "dismissed",
  "expired",
]);
export type ReviewStatus = z.infer<typeof reviewStatusSchema>;

/** A threaded review comment. */
export const reviewCommentSchema = z
  .object({
    id: z.string().min(1),
    review_id: z.string().min(1),
    author_id: z.string().min(1),
    file_path: z.string().min(1),
    line_number: z.number().int().nonnegative(),
    body: z.string().min(1),
    parent_id: z.string().optional(),
    resolved: z.boolean().default(false),
    created_at: z.iso.datetime(),
    updated_at: z.iso.datetime().optional(),
  })
  .strict();
export type ReviewComment = z.infer<typeof reviewCommentSchema>;

/** Digest-bound approval with expiry and separation of duties. */
export const reviewApprovalSchema = z
  .object({
    id: z.string().min(1),
    review_id: z.string().min(1),
    approver_id: z.string().min(1),
    artifact_digest: z.string().min(64).max(64),
    scope: z.string().min(1),
    environment: z.string().min(1),
    status: reviewStatusSchema,
    expires_at: z.iso.datetime(),
    created_at: z.iso.datetime(),
    is_stale: z.boolean().default(false),
  })
  .strict();
export type ReviewApproval = z.infer<typeof reviewApprovalSchema>;

/** Pull request state. */
export const pullRequestStateSchema = z.enum(["open", "closed", "merged", "draft"]);
export type PullRequestState = z.infer<typeof pullRequestStateSchema>;

/** SCM provider for pull requests. */
export const prProviderSchema = z.enum(["github", "gitlab"]);
export type PrProvider = z.infer<typeof prProviderSchema>;

/** Pull request descriptor. */
export const pullRequestSchema = z
  .object({
    id: z.string().min(1),
    organization_id: z.uuid(),
    provider: prProviderSchema,
    repository: z.string().min(1),
    pr_number: z.number().int().positive(),
    title: z.string().min(1),
    description: z.string().default(""),
    source_branch: z.string().min(1),
    target_branch: z.string().min(1),
    state: pullRequestStateSchema,
    author_id: z.string().min(1),
    head_sha: z.string().min(1),
    approvals: z.array(reviewApprovalSchema).default([]),
    comments: z.array(reviewCommentSchema).default([]),
    created_at: z.iso.datetime(),
    updated_at: z.iso.datetime().optional(),
    merged_at: z.iso.datetime().optional(),
  })
  .strict();
export type PullRequest = z.infer<typeof pullRequestSchema>;

/** Request to create a pull request. */
export const createPullRequestSchema = z
  .object({
    provider: prProviderSchema,
    repository: z.string().min(1),
    title: z.string().min(1),
    description: z.string().default(""),
    source_branch: z.string().min(1),
    target_branch: z.string().min(1),
    head_sha: z.string().min(1),
  })
  .strict();
export type CreatePullRequest = z.infer<typeof createPullRequestSchema>;

/** Request to submit an approval. */
export const submitApprovalRequestSchema = z
  .object({
    artifact_digest: z.string().min(64).max(64),
    scope: z.string().min(1),
    environment: z.string().min(1),
    expires_in_hours: z.number().int().positive().default(24),
  })
  .strict();
export type SubmitApprovalRequest = z.infer<typeof submitApprovalRequestSchema>;

/** Request to add a review comment. */
export const addCommentRequestSchema = z
  .object({
    file_path: z.string().min(1),
    line_number: z.number().int().nonnegative(),
    body: z.string().min(1),
    parent_id: z.string().optional(),
  })
  .strict();
export type AddCommentRequest = z.infer<typeof addCommentRequestSchema>;

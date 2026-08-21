import { z } from "zod";

/** Supported source-control providers. */
export const scmProviderSchema = z.enum(["github", "gitlab"]);
export type ScmProvider = z.infer<typeof scmProviderSchema>;

/** Repository visibility classification. */
export const repositoryVisibilitySchema = z.enum(["public", "internal", "private"]);
export type RepositoryVisibility = z.infer<typeof repositoryVisibilitySchema>;

/** Matches standard Git commit SHAs (40-character SHA-1 or 64-character SHA-256). */
export const COMMIT_SHA_PATTERN = /^(?:[0-9a-f]{40}|[0-9a-f]{64})$/;

/** Immutable repository metadata across providers. */
export const repositoryDescriptorSchema = z
  .object({
    provider: scmProviderSchema,
    id: z.string().min(1),
    owner: z.string().min(1),
    name: z.string().min(1),
    full_name: z.string().min(1),
    default_branch: z.string().min(1),
    visibility: repositoryVisibilitySchema,
    clone_url_http: z.url(),
    clone_url_ssh: z.string().min(1),
    is_archived: z.boolean().default(false),
  })
  .strict();
export type RepositoryDescriptor = z.infer<typeof repositoryDescriptorSchema>;

/** Resolved immutable commit details. */
export const commitResolutionSchema = z
  .object({
    provider: scmProviderSchema,
    repository_id: z.string().min(1),
    commit_sha: z.string().regex(COMMIT_SHA_PATTERN),
    ref_requested: z.string().min(1).optional(),
    message: z.string(),
    author_name: z.string(),
    author_email: z.string(),
    authored_at: z.iso.datetime(),
    parent_shas: z.array(z.string().regex(COMMIT_SHA_PATTERN)),
  })
  .strict();
export type CommitResolution = z.infer<typeof commitResolutionSchema>;

/** Normalized webhook event types. */
export const webhookEventTypeSchema = z.enum(["push", "pull_request", "ping"]);
export type WebhookEventType = z.infer<typeof webhookEventTypeSchema>;

/** Provider-neutral normalized webhook payload. */
export const normalizedWebhookEventSchema = z
  .object({
    provider: scmProviderSchema,
    event_id: z.string().min(1),
    event_type: webhookEventTypeSchema,
    repository_full_name: z.string().min(1),
    ref: z.string().optional(),
    before_sha: z.string().regex(COMMIT_SHA_PATTERN).optional(),
    after_sha: z.string().regex(COMMIT_SHA_PATTERN).optional(),
    pr_number: z.number().int().positive().optional(),
    action: z.string().optional(),
    sender: z.string().min(1),
    timestamp: z.iso.datetime(),
  })
  .strict();
export type NormalizedWebhookEvent = z.infer<typeof normalizedWebhookEventSchema>;

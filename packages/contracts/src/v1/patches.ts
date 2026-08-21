import { z } from "zod";

/** Hunk operation lines within a file patch. */
export const patchHunkSchema = z
  .object({
    old_start: z.number().int().nonnegative(),
    old_lines: z.number().int().nonnegative(),
    new_start: z.number().int().nonnegative(),
    new_lines: z.number().int().nonnegative(),
    lines: z.array(z.string()),
  })
  .strict();
export type PatchHunk = z.infer<typeof patchHunkSchema>;

/** Individual file patch operation within a proposal. */
export const filePatchSchema = z
  .object({
    path: z.string().min(1),
    operation: z.enum(["add", "modify", "delete", "rename"]),
    old_path: z.string().optional(),
    hunks: z.array(patchHunkSchema).default([]),
    old_sha: z.string().optional(),
    new_sha: z.string().optional(),
  })
  .strict();
export type FilePatch = z.infer<typeof filePatchSchema>;

/** Proposal containing one or more file patches bound to a content-addressed SHA-256 digest. */
export const patchProposalSchema = z
  .object({
    id: z.string().min(1),
    organization_id: z.uuid(),
    work_package_id: z.string().min(1),
    summary: z.string().min(1),
    digest_sha256: z.string().regex(/^[a-f0-9]{64}$/i),
    files: z.array(filePatchSchema),
    created_at: z.iso.datetime(),
  })
  .strict();
export type PatchProposal = z.infer<typeof patchProposalSchema>;

/** Merge conflict description when applying a patch. */
export const mergeConflictSchema = z
  .object({
    path: z.string().min(1),
    reason: z.string().min(1),
    expected_content: z.string().optional(),
    actual_content: z.string().optional(),
  })
  .strict();
export type MergeConflict = z.infer<typeof mergeConflictSchema>;

/** Result of applying a patch proposal against a repository or worktree. */
export const patchApplicationResultSchema = z
  .object({
    proposal_id: z.string().min(1),
    applied: z.boolean(),
    conflicts: z.array(mergeConflictSchema).default([]),
    committed_sha: z.string().optional(),
  })
  .strict();
export type PatchApplicationResult = z.infer<typeof patchApplicationResultSchema>;

/** Request payload to create a patch proposal. */
export const createPatchProposalRequestSchema = z
  .object({
    work_package_id: z.string().min(1),
    summary: z.string().min(1),
    files: z.array(filePatchSchema),
  })
  .strict();
export type CreatePatchProposalRequest = z.infer<typeof createPatchProposalRequestSchema>;

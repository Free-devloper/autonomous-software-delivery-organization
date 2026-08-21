import { z } from "zod";

import { COMMIT_SHA_PATTERN } from "./scm";

/** File tree item type. */
export const fileEntryTypeSchema = z.enum(["file", "directory", "symlink"]);
export type FileEntryType = z.infer<typeof fileEntryTypeSchema>;

/** Represents a single entry in a repository file tree. */
export const fileEntrySchema = z
  .object({
    name: z.string().min(1),
    path: z.string(),
    type: fileEntryTypeSchema,
    size_bytes: z.number().int().nonnegative(),
  })
  .strict();
export type FileEntry = z.infer<typeof fileEntrySchema>;

/** Response for file tree browsing at a commit. */
export const fileTreeResponseSchema = z
  .object({
    commit_sha: z.string().regex(COMMIT_SHA_PATTERN),
    path: z.string(),
    entries: z.array(fileEntrySchema),
  })
  .strict();
export type FileTreeResponse = z.infer<typeof fileTreeResponseSchema>;

/** Response for file blob inspection. */
export const fileContentResponseSchema = z
  .object({
    commit_sha: z.string().regex(COMMIT_SHA_PATTERN),
    path: z.string().min(1),
    content: z.string(),
    is_binary: z.boolean(),
    size_bytes: z.number().int().nonnegative(),
    lines_count: z.number().int().nonnegative(),
  })
  .strict();
export type FileContentResponse = z.infer<typeof fileContentResponseSchema>;

/** Individual match from lexical search. */
export const lexicalSearchMatchSchema = z
  .object({
    path: z.string().min(1),
    line_number: z.number().int().positive(),
    line_content: z.string(),
  })
  .strict();
export type LexicalSearchMatch = z.infer<typeof lexicalSearchMatchSchema>;

/** Response for lexical search across repository files. */
export const lexicalSearchResultSchema = z
  .object({
    commit_sha: z.string().regex(COMMIT_SHA_PATTERN),
    query: z.string().min(1),
    total_matches: z.number().int().nonnegative(),
    matches: z.array(lexicalSearchMatchSchema),
  })
  .strict();
export type LexicalSearchResult = z.infer<typeof lexicalSearchResultSchema>;

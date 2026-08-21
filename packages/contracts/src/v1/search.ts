import { z } from "zod";

import { COMMIT_SHA_PATTERN } from "./scm";

/** Search retrieval mode across the repository index. */
export const searchModeSchema = z.enum(["lexical", "semantic", "hybrid"]);
export type SearchMode = z.infer<typeof searchModeSchema>;

/** Individual ranked search result from hybrid or semantic retrieval. */
export const searchResultItemSchema = z
  .object({
    chunk_id: z.string().min(1),
    file_path: z.string().min(1),
    start_line: z.number().int().positive(),
    end_line: z.number().int().positive(),
    content: z.string(),
    chunk_type: z.enum(["code", "doc"]),
    score: z.number().min(0),
    lexical_rank: z.number().int().positive().optional(),
    semantic_rank: z.number().int().positive().optional(),
  })
  .strict();
export type SearchResultItem = z.infer<typeof searchResultItemSchema>;

/** Request payload for hybrid or semantic code search. */
export const hybridSearchRequestSchema = z
  .object({
    commit_sha: z.string().regex(COMMIT_SHA_PATTERN),
    query: z.string().min(1),
    mode: searchModeSchema.default("hybrid"),
    limit: z.number().int().positive().max(100).default(20),
  })
  .strict();
export type HybridSearchRequest = z.infer<typeof hybridSearchRequestSchema>;

/** Response payload for hybrid search. */
export const hybridSearchResponseSchema = z
  .object({
    commit_sha: z.string().regex(COMMIT_SHA_PATTERN),
    query: z.string().min(1),
    mode: searchModeSchema,
    total_results: z.number().int().nonnegative(),
    results: z.array(searchResultItemSchema),
  })
  .strict();
export type HybridSearchResponse = z.infer<typeof hybridSearchResponseSchema>;

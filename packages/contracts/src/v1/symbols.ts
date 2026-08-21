import { z } from "zod";

import { COMMIT_SHA_PATTERN } from "./scm";

/** Standard symbol classifications across supported programming languages. */
export const symbolKindSchema = z.enum([
  "function",
  "method",
  "class",
  "interface",
  "variable",
  "constant",
  "type_alias",
  "import",
]);
export type SymbolKind = z.infer<typeof symbolKindSchema>;

/** Precise location coordinates within a source file. */
export const symbolLocationSchema = z
  .object({
    start_line: z.number().int().positive(),
    start_column: z.number().int().nonnegative(),
    end_line: z.number().int().positive(),
    end_column: z.number().int().nonnegative(),
  })
  .strict();
export type SymbolLocation = z.infer<typeof symbolLocationSchema>;

/** Extracted symbol metadata with hierarchy and export status. */
export const codeSymbolSchema = z
  .object({
    id: z.string().min(1),
    name: z.string().min(1),
    qualified_name: z.string().min(1),
    kind: symbolKindSchema,
    location: symbolLocationSchema,
    docstring: z.string().optional(),
    is_exported: z.boolean().default(false),
    parent_id: z.string().optional(),
  })
  .strict();
export type CodeSymbol = z.infer<typeof codeSymbolSchema>;

/** Response payload for symbols extracted from a repository file. */
export const fileSymbolsResponseSchema = z
  .object({
    commit_sha: z.string().regex(COMMIT_SHA_PATTERN),
    file_path: z.string().min(1),
    language: z.string().min(1),
    symbols: z.array(codeSymbolSchema),
  })
  .strict();
export type FileSymbolsResponse = z.infer<typeof fileSymbolsResponseSchema>;

import { describe, expect, it } from "vitest";

import {
  hybridSearchRequestSchema,
  hybridSearchResponseSchema,
  searchModeSchema,
  searchResultItemSchema,
} from "../src/index";

describe("Search contracts", () => {
  const sampleSha = "e4d909c290d0fb1ca068ffaddf22cbd0adddefec";

  it("validates hybrid search request schema", () => {
    const req = {
      commit_sha: sampleSha,
      query: "authentication flow",
      mode: "hybrid" as const,
      limit: 10,
    };
    expect(hybridSearchRequestSchema.parse(req)).toEqual(req);
  });

  it("validates search result item schema", () => {
    const item = {
      chunk_id: "chk_018f",
      file_path: "src/auth/jwt.ts",
      start_line: 12,
      end_line: 45,
      content: "export function verifyJwt() { ... }",
      chunk_type: "code" as const,
      score: 0.85,
      lexical_rank: 1,
      semantic_rank: 2,
    };
    expect(searchResultItemSchema.parse(item)).toEqual(item);
  });

  it("validates hybrid search response schema", () => {
    const res = {
      commit_sha: sampleSha,
      query: "authentication flow",
      mode: "hybrid" as const,
      total_results: 1,
      results: [
        {
          chunk_id: "chk_018f",
          file_path: "src/auth/jwt.ts",
          start_line: 12,
          end_line: 45,
          content: "export function verifyJwt() { ... }",
          chunk_type: "code" as const,
          score: 0.85,
        },
      ],
    };
    expect(hybridSearchResponseSchema.parse(res)).toEqual(res);
  });

  it("rejects invalid search mode", () => {
    expect(() => searchModeSchema.parse("invalid_mode")).toThrow();
  });
});

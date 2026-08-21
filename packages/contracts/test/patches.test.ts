import { describe, expect, it } from "vitest";

import {
  createPatchProposalRequestSchema,
  filePatchSchema,
  mergeConflictSchema,
  patchApplicationResultSchema,
  patchHunkSchema,
  patchProposalSchema,
} from "../src/index";

describe("Patch contracts", () => {
  const timestamp = "2026-08-20T12:00:00.000Z";
  const dummySha256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";

  it("validates patch hunk and file patch schemas", () => {
    const hunk = {
      old_start: 1,
      old_lines: 3,
      new_start: 1,
      new_lines: 4,
      lines: [" import os", "-print('old')", "+print('new')", "+print('extra')"],
    };
    expect(patchHunkSchema.parse(hunk)).toEqual(hunk);

    const filePatch = {
      path: "src/main.py",
      operation: "modify" as const,
      hunks: [hunk],
      old_sha: "abc1234",
      new_sha: "def5678",
    };
    expect(filePatchSchema.parse(filePatch)).toEqual(filePatch);
  });

  it("validates patch proposal with SHA-256 digest", () => {
    const proposal = {
      id: "patch-001",
      organization_id: "018f0000-0000-7000-8000-000000000001",
      work_package_id: "pkg-1",
      summary: "Add telemetry instrumentation",
      digest_sha256: dummySha256,
      files: [
        {
          path: "src/telemetry.py",
          operation: "add" as const,
          hunks: [],
        },
      ],
      created_at: timestamp,
    };
    expect(patchProposalSchema.parse(proposal)).toEqual(proposal);

    // Invalid SHA-256 format should throw
    expect(() =>
      patchProposalSchema.parse({
        ...proposal,
        digest_sha256: "not-a-valid-64-char-hex-digest",
      }),
    ).toThrow();
  });

  it("validates patch application results and merge conflicts", () => {
    const conflict = {
      path: "src/config.py",
      reason: "Hunk #1 failed to apply: expected content mismatch",
      expected_content: "DEBUG = False",
      actual_content: "DEBUG = True",
    };
    expect(mergeConflictSchema.parse(conflict)).toEqual(conflict);

    const successResult = {
      proposal_id: "patch-001",
      applied: true,
      conflicts: [],
      committed_sha: "deadbeef1234567890abcdef1234567890abcdef",
    };
    expect(patchApplicationResultSchema.parse(successResult)).toEqual(successResult);

    const conflictResult = {
      proposal_id: "patch-001",
      applied: false,
      conflicts: [conflict],
    };
    expect(patchApplicationResultSchema.parse(conflictResult)).toEqual(conflictResult);
  });

  it("validates create patch proposal request payload", () => {
    const createReq = {
      work_package_id: "pkg-1",
      summary: "Fix memory leak in subscriber queue",
      files: [
        {
          path: "src/queue.py",
          operation: "modify" as const,
          hunks: [],
        },
      ],
    };
    expect(createPatchProposalRequestSchema.parse(createReq)).toEqual(createReq);
  });
});
